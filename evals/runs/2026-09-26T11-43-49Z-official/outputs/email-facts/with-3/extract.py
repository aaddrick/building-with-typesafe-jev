"""Read a customer email with TypeSafe's Jev model.

Reports how many distinct products the customer says are defective, and
whether the delivery date they were promised has already passed.

Calendar math (resolving "next Thursday" or "August 14" into an actual date,
and comparing it to `today`) is done in code, not by the model: Jev only
reads what the email says about the date, per TypeSafe's date-extraction
pattern (https://docs.typesafe.ai/cookbooks/date_extraction_cookbook).
"""

from __future__ import annotations

from datetime import date, timedelta

from typesafe_sdk import Choice, Score, TypeSafeClient

MONTHS = {
    name: i
    for i, name in enumerate(
        [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ],
        start=1,
    )
}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Score levels are indexed by position (0, 1, 2, ...), so the rounded score
# doubles as the product count. The top level absorbs anything higher, since
# a customer email realistically won't complain about more than a handful of
# distinct products.
DEFECTIVE_PRODUCT_COUNT_LEVELS = [
    "The customer does not describe any product as defective.",
    "The customer describes exactly one product as defective.",
    "The customer describes exactly two different products as defective.",
    "The customer describes exactly three different products as defective.",
    "The customer describes exactly four different products as defective.",
    "The customer describes five or more different products as defective.",
]


def _promised_delivery_date_questions() -> dict[str, Choice]:
    """Questions that read (but don't calculate) the promised delivery date."""
    return {
        "delivery_date_mode": Choice(
            instructions=(
                "How is the delivery date the customer was promised written? "
                "'absolute' = a calendar date naming a month; "
                "'relative' = relative to today (e.g. a weekday, 'tomorrow'); "
                "'none' = no promised delivery date is stated in the email"
            ),
            criteria={"absolute": None, "relative": None, "none": None},
        ),
        "delivery_month": Choice(
            instructions="If the promised delivery date is absolute, which month is it in?",
            criteria={m: None for m in MONTHS} | {"none": "Not applicable"},
        ),
        "delivery_day": Choice(
            instructions="If the promised delivery date is absolute, which day of the month (1-31)?",
            criteria={str(d): None for d in range(1, 32)} | {"none": "Not applicable"},
        ),
        "delivery_year": Choice(
            instructions=(
                "If the promised delivery date is absolute, which year? "
                "'none' if unstated; 'out_of_range' if stated but outside 1900-2050"
            ),
            criteria={str(y): None for y in range(1900, 2051)}
            | {"out_of_range": None, "none": None},
        ),
        "delivery_day_anchor": Choice(
            instructions=(
                "If the promised delivery date is relative, which day is it? "
                "'today', 'tomorrow', 'day_after', or 'weekday' (a named day)"
            ),
            criteria={
                "today": None, "tomorrow": None, "day_after": None,
                "weekday": None, "none": "Not applicable",
            },
        ),
        "delivery_weekday": Choice(
            instructions="If a weekday is named for the promised delivery date, which one?",
            criteria={w: None for w in WEEKDAYS} | {"none": "Not applicable"},
        ),
        "delivery_week_offset": Choice(
            instructions=(
                "If a weekday is named for the promised delivery date, which week? "
                "'current' = this week; 'next' = the following week; "
                "'none' = a bare weekday with no week stated"
            ),
            criteria={"current": None, "next": None, "none": "Not applicable"},
        ),
    }


def _resolve_weekday(today: date, weekday: str, week_offset: str) -> date:
    target = WEEKDAYS.index(weekday)
    this_monday = today - timedelta(days=today.weekday())
    if week_offset == "next":
        return this_monday + timedelta(days=7 + target)
    if week_offset == "current":
        return this_monday + timedelta(days=target)
    # Bare weekday: the next occurrence on or after today.
    return today + timedelta(days=(target - today.weekday()) % 7)


def _resolve_promised_delivery_date(answers: dict, today: date) -> date | None:
    mode = answers["delivery_date_mode"].choice
    if mode == "absolute":
        month, day, year = (
            answers["delivery_month"].choice,
            answers["delivery_day"].choice,
            answers["delivery_year"].choice,
        )
        if month == "none" or day == "none" or year == "out_of_range":
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
        anchor = answers["delivery_day_anchor"].choice
        if anchor == "today":
            return today
        if anchor == "tomorrow":
            return today + timedelta(days=1)
        if anchor == "day_after":
            return today + timedelta(days=2)
        if anchor == "weekday":
            weekday = answers["delivery_weekday"].choice
            if weekday not in WEEKDAYS:
                return None
            return _resolve_weekday(today, weekday, answers["delivery_week_offset"].choice)
    return None


def check_email(email_text: str, today: date) -> dict:
    """Ask Jev about a customer email and combine the answers with code.

    Returns a dict with:
      - "defective_product_count": how many different products the
        customer says are defective.
      - "promised_delivery_date": the delivery date the email promises,
        resolved to an actual `date`, or None if the email doesn't state one.
      - "delivery_date_passed": whether that promised date is before `today`.
    """
    with TypeSafeClient() as client:
        response = client.system_one(
            state={"email": email_text},
            questions={
                "defective_product_count": Score(
                    instructions=(
                        "Considering only products the customer says are defective, "
                        "broken, faulty, or not working, how many different products "
                        "does `email` report as defective? Count each distinct "
                        "product once even if it's mentioned more than once."
                    ),
                    criteria=DEFECTIVE_PRODUCT_COUNT_LEVELS,
                ),
                **_promised_delivery_date_questions(),
            },
        )

    answers = response.answers

    max_level = len(DEFECTIVE_PRODUCT_COUNT_LEVELS) - 1
    raw_count_score = answers["defective_product_count"].score
    defective_product_count = round(max(0.0, min(raw_count_score, max_level)))

    promised_delivery_date = _resolve_promised_delivery_date(answers, today)
    delivery_date_passed = (
        promised_delivery_date is not None and promised_delivery_date < today
    )

    return {
        "defective_product_count": defective_product_count,
        "promised_delivery_date": promised_delivery_date,
        "delivery_date_passed": delivery_date_passed,
    }
