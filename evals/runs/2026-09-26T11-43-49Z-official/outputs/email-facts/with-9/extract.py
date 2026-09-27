"""Read a customer email with TypeSafe's Jev model.

Reports how many distinct products the customer says are defective, and
whether the delivery date they were promised has already passed. Jev reads
what the email says; date and count arithmetic stay in code.
"""

import datetime

from typesafe_sdk import Choice, TypeSafeClient

MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Choice needs a fixed, enumerable option set, so the count is bucketed rather
# than open-ended. Customer emails rarely name more than a handful of products.
PRODUCT_COUNT_LABELS = {"0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5_or_more": 5}

DELIVERY_DATE_ROLE = "the delivery date the customer was promised (when the order was due to arrive)"


def _product_count_question() -> Choice:
    return Choice(
        instructions=(
            "How many different products does the customer say are defective, broken, "
            "faulty, or otherwise not working? Count each distinct product once even if "
            "it is mentioned more than once. Do not count products the customer is only "
            "asking about, praising, or ordering with no complaint."
        ),
        criteria={
            "0": "No product is described as defective.",
            "1": "Exactly one distinct defective product.",
            "2": "Exactly two distinct defective products.",
            "3": "Exactly three distinct defective products.",
            "4": "Exactly four distinct defective products.",
            "5_or_more": "Five or more distinct defective products.",
        },
    )


def _delivery_date_questions(today: datetime.date) -> dict[str, Choice]:
    """Choice questions that read the promised delivery date's shape and parts.

    Modeled on TypeSafe's date-extraction pattern: Jev names what the text
    says, code resolves that into a concrete date. The model never does
    calendar math.
    """
    role = DELIVERY_DATE_ROLE
    absent = "The email does not state this, or it is not this kind of date."
    year_window = range(today.year - 2, today.year + 3)
    return {
        "mode": Choice(
            instructions=(
                f"How is {role} written, if at all? 'absolute' = a calendar date naming a "
                "month (e.g. 'August 14', 'the 3rd of March'); 'relative' = given relative to "
                "today (today, tomorrow, the day after tomorrow, or a named weekday such as "
                "'next Thursday'); 'none' = the email never states a promised delivery date."
            ),
            criteria={"absolute": None, "relative": None, "none": None},
        ),
        "month": Choice(
            instructions=f"If {role} is an absolute calendar date, which month is it in?",
            criteria={m: None for m in MONTHS} | {"none": absent},
        ),
        "day": Choice(
            instructions=f"If {role} is an absolute calendar date, which day of the month (1-31)?",
            criteria={str(d): None for d in range(1, 32)} | {"none": absent},
        ),
        "year": Choice(
            instructions=(
                f"If {role} is an absolute calendar date, which year? Pick 'none' if the email "
                "states no year (code infers it), or 'out_of_range' if a year is stated but not "
                "in the list."
            ),
            criteria={str(y): None for y in year_window}
            | {
                "out_of_range": "A year is stated for this date but is outside the listed range.",
                "none": "No year is stated for this date.",
            },
        ),
        "day_anchor": Choice(
            instructions=(
                f"If {role} is relative to today, which day is it? 'today', 'tomorrow', "
                "'day_after' (the day after tomorrow), or 'weekday' (a named day of the week)."
            ),
            criteria={
                "today": None,
                "tomorrow": None,
                "day_after": None,
                "weekday": None,
                "none": absent,
            },
        ),
        "weekday": Choice(
            instructions=f"If {role} names a day of the week, which one?",
            criteria={w: None for w in WEEKDAYS} | {"none": absent},
        ),
        "week_offset": Choice(
            instructions=(
                f"If {role} names a weekday, which week is it in? 'next' for 'next Thursday' or "
                "'Thursday next week'; 'current' for 'this Thursday'; 'none' for a bare weekday "
                "with no qualifier (just 'Thursday' / 'on Thursday')."
            ),
            criteria={"current": None, "next": None, "none": absent},
        ),
    }


def _resolve_weekday(today: datetime.date, weekday: str, week_offset: str) -> datetime.date:
    """A bare weekday is the next occurrence on or after today; 'next' is the
    following calendar week; 'current' is this week."""
    w = WEEKDAYS.index(weekday)
    this_monday = today - datetime.timedelta(days=today.weekday())
    if week_offset == "next":
        return this_monday + datetime.timedelta(days=7 + w)
    if week_offset == "current":
        return this_monday + datetime.timedelta(days=w)
    return today + datetime.timedelta(days=(w - today.weekday()) % 7)


def _assemble_delivery_date(
    answers: dict, today: datetime.date
) -> tuple[datetime.date | None, float | None]:
    """Resolve the date-part answers into a concrete date and a confidence
    (the lowest confidence among the parts actually used), or (None, conf)
    if the email never states this date or the parts don't add up."""
    mode = answers["mode"].choice
    confidences = [answers["mode"].confidence]

    if mode == "none":
        return None, answers["mode"].confidence

    if mode == "absolute":
        month, day, year = answers["month"].choice, answers["day"].choice, answers["year"].choice
        confidences += [answers["month"].confidence, answers["day"].confidence, answers["year"].confidence]
        if "none" in (month, day) or not day.isdigit() or month not in MONTHS:
            return None, min(confidences)
        if year == "out_of_range":
            return None, min(confidences)
        try:
            if year == "none":
                resolved = datetime.date(today.year, MONTHS[month], int(day))
                if resolved < today - datetime.timedelta(days=31):
                    resolved = datetime.date(today.year + 1, MONTHS[month], int(day))
            else:
                resolved = datetime.date(int(year), MONTHS[month], int(day))
        except ValueError:
            return None, min(confidences)
        return resolved, min(confidences)

    if mode == "relative":
        anchor = answers["day_anchor"].choice
        confidences.append(answers["day_anchor"].confidence)
        if anchor == "today":
            return today, min(confidences)
        if anchor == "tomorrow":
            return today + datetime.timedelta(days=1), min(confidences)
        if anchor == "day_after":
            return today + datetime.timedelta(days=2), min(confidences)
        if anchor == "weekday":
            weekday, offset = answers["weekday"].choice, answers["week_offset"].choice
            confidences += [answers["weekday"].confidence, answers["week_offset"].confidence]
            if weekday not in WEEKDAYS:
                return None, min(confidences)
            return _resolve_weekday(today, weekday, offset), min(confidences)
        return None, min(confidences)

    return None, min(confidences)


def check_email(email_text: str, today: datetime.date) -> dict:
    """Read a customer email with Jev and report:

    - defective_product_count: how many distinct products the customer says
      are defective (bucketed 0-5, where 5 means "5 or more").
    - promised_delivery_date: the delivery date Jev read from the email, or
      None if the email never states one.
    - delivery_date_passed: whether that date is before `today`, or None if
      no promised delivery date could be determined.
    """
    questions = {"defective_product_count": _product_count_question()}
    questions.update(_delivery_date_questions(today))

    with TypeSafeClient() as client:
        response = client.system_one(state=email_text, questions=questions)

    count_answer = response.choices["defective_product_count"]
    defective_product_count = PRODUCT_COUNT_LABELS[count_answer.choice]

    date_part_names = ("mode", "month", "day", "year", "day_anchor", "weekday", "week_offset")
    date_answers = {name: response.choices[name] for name in date_part_names}
    promised_delivery_date, delivery_date_confidence = _assemble_delivery_date(date_answers, today)

    delivery_date_passed = (
        None if promised_delivery_date is None else promised_delivery_date < today
    )

    return {
        "defective_product_count": defective_product_count,
        "defective_product_count_confidence": count_answer.confidence,
        "promised_delivery_date": promised_delivery_date,
        "promised_delivery_date_confidence": delivery_date_confidence,
        "delivery_date_passed": delivery_date_passed,
    }
