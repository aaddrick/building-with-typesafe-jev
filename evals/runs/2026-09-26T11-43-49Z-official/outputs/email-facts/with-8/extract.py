"""Read a customer email with TypeSafe's Jev model.

Reports how many distinct products the customer describes as defective, and
whether the delivery date they were promised has already passed. Jev reads
what the text says (date parts, product mentions); code does the counting,
date assembly, and the comparison against `today`.
"""

from datetime import date, timedelta

from typesafe_sdk import Choice, TypeSafeClient

TYPESAFE_MODEL = "jev-latest"

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
WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
YEAR_WINDOW = list(range(1900, 2051))

DELIVERY_DATE_ROLE = "the delivery date the customer was promised for their order"


def _delivery_date_questions() -> dict[str, Choice]:
    """Seven Choice questions that read the promised delivery date's shape and
    parts off the email text. No calendar math happens here."""
    absent = "The email does not state this, or it is not this kind of date."
    role = DELIVERY_DATE_ROLE
    return {
        "mode": Choice(
            instructions=(
                f"How is {role} written? 'absolute' = a calendar date naming a month "
                "(e.g. 'August 14', 'the 3rd of March'); 'relative' = given relative to "
                "today (today, tomorrow, the day after tomorrow, or a named weekday such "
                "as 'next Thursday'); 'none' = the email does not state this date."
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
                f"If {role} is an absolute calendar date, which year? Pick 'none' if the "
                "email states no year (code infers it), or 'out_of_range' if a year is "
                "stated but not in the list."
            ),
            criteria={str(y): None for y in YEAR_WINDOW}
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
                f"If {role} names a weekday, which week is it in? 'next' for 'next "
                "Thursday' or 'Thursday next week'; 'current' for 'this Thursday'; 'none' "
                "for a bare weekday with no qualifier (just 'Thursday' / 'on Thursday')."
            ),
            criteria={"current": None, "next": None, "none": absent},
        ),
    }


def _product_count_question() -> Choice:
    """One Choice question: the count is a small defined set, not a spectrum."""
    return Choice(
        instructions=(
            "How many different products does the customer describe as defective, "
            "broken, faulty, or otherwise not working in this email? Count each "
            "distinct product once, even if it is mentioned more than once."
        ),
        criteria={
            "0": "No product is described as defective, broken, faulty, or not working.",
            "1": "Exactly one distinct product is described as defective, broken, faulty, or not working.",
            "2": "Exactly two distinct products are described as defective, broken, faulty, or not working.",
            "3": "Exactly three distinct products are described as defective, broken, faulty, or not working.",
            "4_or_more": "Four or more distinct products are described as defective, broken, faulty, or not working.",
        },
    )


def _resolve_weekday(today: date, weekday: str, week_offset: str) -> date:
    """A bare weekday is the next occurrence on or after today; 'next' is the
    following calendar week; 'current' is this week."""
    w = WEEKDAYS.index(weekday)
    this_monday = today - timedelta(days=today.weekday())
    if week_offset == "next":
        return this_monday + timedelta(days=7 + w)
    if week_offset == "current":
        return this_monday + timedelta(days=w)
    return today + timedelta(days=(w - today.weekday()) % 7)


def _assemble_delivery_date(choices: dict[str, str], today: date) -> date | None:
    """Turn Jev's read of the date's parts into a concrete date, in code."""
    mode = choices["mode"]

    if mode == "absolute":
        month, day, year = choices["month"], choices["day"], choices["year"]
        if "none" in (month, day) or not day.isdigit() or month not in MONTHS:
            return None
        if year == "out_of_range":
            return None
        if year == "none":
            try:
                resolved = date(today.year, MONTHS[month], int(day))
            except ValueError:
                return None
            if resolved < today - timedelta(days=31):
                resolved = date(today.year + 1, MONTHS[month], int(day))
            return resolved
        try:
            return date(int(year), MONTHS[month], int(day))
        except ValueError:
            return None

    if mode == "relative":
        anchor = choices["day_anchor"]
        if anchor == "today":
            return today
        if anchor == "tomorrow":
            return today + timedelta(days=1)
        if anchor == "day_after":
            return today + timedelta(days=2)
        if anchor == "weekday":
            weekday, offset = choices["weekday"], choices["week_offset"]
            if weekday not in WEEKDAYS:
                return None
            return _resolve_weekday(today, weekday, offset)
        return None

    return None


def check_email(email_text: str, today: date) -> dict:
    """Read a customer email and report defect count and delivery-date status.

    Returns a dict with:
      - "defective_product_count": int, number of distinct products the
        customer says are defective (4 means "4 or more").
      - "promised_delivery_date": date | None, the delivery date Jev read off
        the email, resolved against `today`, or None if the email doesn't
        state one.
      - "delivery_date_passed": bool, whether that promised date is before
        `today`. False when no delivery date is stated.
    """
    questions = {**_delivery_date_questions(), "product_count": _product_count_question()}

    with TypeSafeClient() as client:
        answers = client.system_one(
            state=email_text, questions=questions, model=TYPESAFE_MODEL
        ).answers

    choices = {name: answer.choice for name, answer in answers.items()}

    product_count_choice = choices["product_count"]
    defective_product_count = (
        4 if product_count_choice == "4_or_more" else int(product_count_choice)
    )

    promised_delivery_date = _assemble_delivery_date(choices, today)
    delivery_date_passed = (
        promised_delivery_date is not None and promised_delivery_date < today
    )

    return {
        "defective_product_count": defective_product_count,
        "promised_delivery_date": promised_delivery_date,
        "delivery_date_passed": delivery_date_passed,
    }
