import datetime

from typesafe_sdk import Choice, Score, TypeSafeClient

_client = TypeSafeClient()

_MODEL = "jev-latest"

_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_YEARS = [str(y) for y in range(1900, 2051)]

# Below this, treat the model's read of the delivery-date "mode" as too
# uncertain to act on and report "unknown" rather than guessing.
_MODE_CONFIDENCE_THRESHOLD = 0.6


def _defective_product_question() -> Score:
    return Score(
        instructions=(
            "How many different products does the customer describe as "
            "defective, broken, faulty, or otherwise not working as expected?"
        ),
        criteria=[
            "No product is described as defective",
            "Exactly one product is described as defective",
            "Exactly two different products are described as defective",
            "Exactly three different products are described as defective",
            "Four or more different products are described as defective",
        ],
    )


def _delivery_date_questions() -> dict:
    return {
        "mode": Choice(
            instructions=(
                "How is the promised delivery date (the date the customer was "
                "told their order/product would arrive) expressed in the "
                "email, if it is mentioned at all?"
            ),
            criteria={
                "absolute": "A specific calendar date is given, e.g. 'August 14' or '8/14/2026'",
                "relative": "The date is relative to today, e.g. 'tomorrow', 'in two days', 'next Tuesday'",
                "none": "No promised delivery date is mentioned anywhere in the email",
            },
        ),
        "month": Choice(
            instructions="If an absolute delivery date is given, which month is it?",
            criteria={**{m: m for m in _MONTHS}, "none": "No absolute date, or month not stated"},
        ),
        "day": Choice(
            instructions="If an absolute delivery date is given, which day of the month is it?",
            criteria={**{str(d): str(d) for d in range(1, 32)}, "none": "No absolute date, or day not stated"},
        ),
        "year": Choice(
            instructions="If an absolute delivery date is given, which year is it?",
            criteria={
                **{y: y for y in _YEARS},
                "none": "No year stated",
                "out_of_range": "A year outside 1900-2050 is stated",
            },
        ),
        "day_anchor": Choice(
            instructions="If a relative delivery date is given, what is it relative to?",
            criteria={
                "today": "Delivery was promised for today",
                "tomorrow": "Delivery was promised for tomorrow",
                "day_after": "Delivery was promised for the day after tomorrow",
                "weekday": "Delivery was promised for a named day of the week",
                "none": "Not a relative date",
            },
        ),
        "weekday": Choice(
            instructions="If the relative delivery date names a weekday, which one?",
            criteria={**{w: w for w in _WEEKDAYS}, "none": "No weekday named"},
        ),
        "week_offset": Choice(
            instructions=(
                "If a weekday is named for the relative delivery date, is it "
                "this coming week ('current'), the week after ('next'), or "
                "was no week specified (bare weekday, meaning its next "
                "occurrence)?"
            ),
            criteria={
                "current": "Explicitly this week",
                "next": "Explicitly next week",
                "none": "No week qualifier given, or not applicable",
            },
        ),
    }


def _resolve_weekday(today: datetime.date, weekday: str, week_offset: str) -> datetime.date:
    target = _WEEKDAYS.index(weekday)
    this_monday = today - datetime.timedelta(days=today.weekday())
    if week_offset == "next":
        return this_monday + datetime.timedelta(days=7 + target)
    if week_offset == "current":
        return this_monday + datetime.timedelta(days=target)
    return today + datetime.timedelta(days=(target - today.weekday()) % 7)


def _resolve_delivery_date(answers: dict, today: datetime.date) -> datetime.date | None:
    mode_answer = answers["mode"]
    if mode_answer.confidence < _MODE_CONFIDENCE_THRESHOLD:
        return None

    mode = mode_answer.choice
    if mode == "none":
        return None

    if mode == "absolute":
        month_name = answers["month"].choice
        day_str = answers["day"].choice
        year_str = answers["year"].choice
        if month_name == "none" or day_str == "none":
            return None

        month = _MONTHS.index(month_name) + 1
        day = int(day_str)

        if year_str in ("none", "out_of_range"):
            year = today.year
            try:
                candidate = datetime.date(year, month, day)
            except ValueError:
                return None
            if (today - candidate).days > 30:
                year += 1
        else:
            year = int(year_str)

        try:
            return datetime.date(year, month, day)
        except ValueError:
            return None

    if mode == "relative":
        anchor = answers["day_anchor"].choice
        if anchor == "today":
            return today
        if anchor == "tomorrow":
            return today + datetime.timedelta(days=1)
        if anchor == "day_after":
            return today + datetime.timedelta(days=2)
        if anchor == "weekday":
            weekday_name = answers["weekday"].choice
            if weekday_name == "none":
                return None
            return _resolve_weekday(today, weekday_name, answers["week_offset"].choice)

    return None


def check_email(email_text: str, today: datetime.date) -> dict:
    response = _client.system_one(
        state=email_text,
        questions={
            "defective_count": _defective_product_question(),
            **_delivery_date_questions(),
        },
        model=_MODEL,
    )
    answers = response.answers

    defective_product_count = max(0, round(answers["defective_count"].score))

    delivery_date = _resolve_delivery_date(answers, today)
    delivery_date_passed = None if delivery_date is None else delivery_date < today

    return {
        "defective_product_count": defective_product_count,
        "delivery_date_passed": delivery_date_passed,
    }
