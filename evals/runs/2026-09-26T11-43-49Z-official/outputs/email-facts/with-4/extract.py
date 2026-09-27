"""Read a customer email with TypeSafe's Jev model.

Jev only returns typed judgments (Choice/Score/Noul), so this never asks it to
generate a list of product names or do calendar math. It reads a bucketed count
of distinct defective products with a Score, and reads the promised delivery
date's parts with Choice questions; code resolves those parts to a concrete
date and compares it to `today`.
"""

from __future__ import annotations

import datetime

from typesafe_sdk import Choice, Score, TypeSafeClient

MODEL = "jev-latest"

MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

PRODUCT_COUNT_LEVELS = [
    "No products are described as defective, broken, or faulty.",
    "Exactly one product is described as defective, broken, or faulty.",
    "Exactly two different products are described as defective, broken, or faulty.",
    "Exactly three different products are described as defective, broken, or faulty.",
    "Four or more different products are described as defective, broken, or faulty.",
]

_DELIVERY_ROLE = "the delivery date the customer says they were promised"


def _delivery_date_questions(today: datetime.date) -> dict[str, Choice]:
    """Choice questions that read the promised delivery date's shape and parts -- no math."""
    absent = "The email does not state this, or it is not this kind of date."
    year_window = range(today.year - 5, today.year + 6)
    role = _DELIVERY_ROLE
    return {
        "date_mode": Choice(
            instructions=(
                f"How is {role} written, if at all? 'absolute' = a calendar date naming a "
                "month (e.g. 'August 14', 'the 3rd of March'); 'relative' = given relative to "
                "today (today, tomorrow, the day after tomorrow, or a named weekday such as "
                "'next Thursday'); 'none' = the email never states this date."
            ),
            criteria={"absolute": None, "relative": None, "none": None},
        ),
        "date_month": Choice(
            instructions=f"If {role} is an absolute calendar date, which month is it in?",
            criteria={m: None for m in MONTHS} | {"none": absent},
        ),
        "date_day": Choice(
            instructions=f"If {role} is an absolute calendar date, which day of the month (1-31)?",
            criteria={str(d): None for d in range(1, 32)} | {"none": absent},
        ),
        "date_year": Choice(
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
        "date_day_anchor": Choice(
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
        "date_weekday": Choice(
            instructions=f"If {role} names a day of the week, which one?",
            criteria={w: None for w in WEEKDAYS} | {"none": absent},
        ),
        "date_week_offset": Choice(
            instructions=(
                f"If {role} names a weekday, which week is it in? 'next' for 'next Thursday' "
                "or 'Thursday next week'; 'current' for 'this Thursday'; 'none' for a bare "
                "weekday with no qualifier (just 'Thursday' / 'on Thursday')."
            ),
            criteria={"current": None, "next": None, "none": absent},
        ),
    }


def _resolve_weekday(today: datetime.date, weekday: str, week_offset: str) -> datetime.date:
    """A bare weekday is the next occurrence on/after today; 'next' is the following calendar
    week; 'current' is this week."""
    w = WEEKDAYS.index(weekday)
    this_monday = today - datetime.timedelta(days=today.weekday())
    if week_offset == "next":
        return this_monday + datetime.timedelta(days=7 + w)
    if week_offset == "current":
        return this_monday + datetime.timedelta(days=w)
    return today + datetime.timedelta(days=(w - today.weekday()) % 7)


def _assemble_delivery_date(choices: dict, today: datetime.date) -> dict:
    """Resolve Jev's date-part answers into a concrete date, in code. Confidence is the
    weakest of the parts actually used."""
    mode = choices["date_mode"].choice
    confidences = [choices["date_mode"].confidence]

    def result(resolved: datetime.date | None) -> dict:
        return {"date": resolved, "confidence": min(confidences)}

    if mode == "none":
        return result(None)

    if mode == "absolute":
        month = choices["date_month"].choice
        day = choices["date_day"].choice
        year = choices["date_year"].choice
        confidences.extend(
            [choices["date_month"].confidence, choices["date_day"].confidence, choices["date_year"].confidence]
        )
        if "none" in (month, day) or not day.isdigit() or month not in MONTHS or year == "out_of_range":
            return result(None)
        if year == "none":
            try:
                resolved = datetime.date(today.year, MONTHS[month], int(day))
            except ValueError:
                return result(None)
            if resolved < today - datetime.timedelta(days=31):
                resolved = datetime.date(today.year + 1, MONTHS[month], int(day))
            return result(resolved)
        try:
            return result(datetime.date(int(year), MONTHS[month], int(day)))
        except ValueError:
            return result(None)

    if mode == "relative":
        anchor = choices["date_day_anchor"].choice
        confidences.append(choices["date_day_anchor"].confidence)
        if anchor == "today":
            return result(today)
        if anchor == "tomorrow":
            return result(today + datetime.timedelta(days=1))
        if anchor == "day_after":
            return result(today + datetime.timedelta(days=2))
        if anchor == "weekday":
            weekday = choices["date_weekday"].choice
            week_offset = choices["date_week_offset"].choice
            confidences.extend([choices["date_weekday"].confidence, choices["date_week_offset"].confidence])
            if weekday not in WEEKDAYS:
                return result(None)
            return result(_resolve_weekday(today, weekday, week_offset))
        return result(None)

    return result(None)


def check_email(email_text: str, today: datetime.date) -> dict:
    """Use Jev to read a customer email for defective-product mentions and a promised
    delivery date, then judge whether that date has already passed relative to `today`."""
    questions: dict = {
        "defective_product_count": Score(
            instructions=(
                "How many different products does the customer say are defective, broken, "
                "or faulty? Count distinct products only once even if mentioned more than once."
            ),
            criteria=PRODUCT_COUNT_LEVELS,
        ),
        **_delivery_date_questions(today),
    }

    with TypeSafeClient() as client:
        response = client.system_one(state=email_text, questions=questions, model=MODEL)

    count_answer = response.scores["defective_product_count"]
    defective_product_count = round(count_answer.score)

    resolved = _assemble_delivery_date(response.choices, today)
    delivery_date = resolved["date"]
    delivery_date_passed = delivery_date < today if delivery_date is not None else None

    return {
        "defective_product_count": defective_product_count,
        "defective_product_count_confidence": count_answer.confidence,
        "delivery_date": delivery_date,
        "delivery_date_confidence": resolved["confidence"],
        "delivery_date_passed": delivery_date_passed,
    }
