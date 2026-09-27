from datetime import date, timedelta

from typesafe_sdk import Choice, Score, TypeSafeClient

_MONTHS = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]
_WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _date_questions(today: date) -> dict:
    year_options = {
        "none": "no year is stated or implied",
        str(today.year - 1): None,
        str(today.year): None,
        str(today.year + 1): None,
    }
    return {
        "date_mode": Choice(
            instructions="How is the delivery date that was promised to the customer expressed in the email?",
            criteria={
                "absolute": "a specific calendar date, e.g. 'March 5' or 'March 5th, 2027'",
                "relative": "expressed relative to `today`, e.g. 'tomorrow', 'in 2 days', 'next Thursday', 'this Friday'",
                "none": "no delivery date was promised or mentioned",
            },
        ),
        "date_month": Choice(
            instructions="If the promised delivery date is an absolute calendar date, which month is it in?",
            criteria={m: None for m in _MONTHS} | {"none": "not applicable or not stated"},
        ),
        "date_day": Choice(
            instructions="If the promised delivery date is an absolute calendar date, which day of the month is it?",
            criteria={f"{d:02d}": None for d in range(1, 32)} | {"none": "not applicable or not stated"},
        ),
        "date_year": Choice(
            instructions="If the promised delivery date is an absolute calendar date, which year is it, if stated?",
            criteria=year_options,
        ),
        "date_anchor": Choice(
            instructions="If the promised delivery date is relative to `today`, which of these best matches it?",
            criteria={
                "today": None,
                "tomorrow": None,
                "day_after_tomorrow": None,
                "weekday": "a specific day of the week, e.g. 'Thursday'",
                "none": "not applicable",
            },
        ),
        "date_weekday": Choice(
            instructions="If the promised delivery date names a day of the week, which one?",
            criteria={w: None for w in _WEEKDAYS} | {"none": "not applicable or not stated"},
        ),
        "date_week_offset": Choice(
            instructions=(
                "If the promised delivery date names a day of the week, is it in the current week "
                "('this Thursday') or the following week ('next Thursday')?"
            ),
            criteria={
                "this": "this coming occurrence of that weekday",
                "next": "the occurrence in the following week",
                "none": "not applicable",
            },
        ),
    }


def _assemble_delivery_date(answers: dict, today: date) -> date | None:
    mode = answers["date_mode"].choice

    if mode == "absolute":
        month_name = answers["date_month"].choice
        day_str = answers["date_day"].choice
        if month_name == "none" or day_str == "none":
            return None
        month = _MONTHS.index(month_name) + 1
        day = int(day_str)
        year_str = answers["date_year"].choice
        if year_str == "none":
            candidate = date(today.year, month, day)
            # No year was stated: assume the current year, but if that date has
            # already gone by, the customer almost certainly meant next year.
            if candidate < today:
                candidate = date(today.year + 1, month, day)
        else:
            candidate = date(int(year_str), month, day)
        return candidate

    if mode == "relative":
        anchor = answers["date_anchor"].choice
        if anchor == "today":
            return today
        if anchor == "tomorrow":
            return today + timedelta(days=1)
        if anchor == "day_after_tomorrow":
            return today + timedelta(days=2)
        if anchor == "weekday":
            weekday_name = answers["date_weekday"].choice
            if weekday_name == "none":
                return None
            target = _WEEKDAYS.index(weekday_name)
            days_ahead = (target - today.weekday()) % 7
            if answers["date_week_offset"].choice == "next":
                days_ahead += 7
            return today + timedelta(days=days_ahead)
        return None

    return None


def check_email(email_text: str, today: date) -> dict:
    with TypeSafeClient() as client:
        response = client.system_one(
            state={"email": email_text, "today": today.isoformat()},
            questions={
                "defective_count": Score(
                    instructions=(
                        "How many different products does the customer say are defective, "
                        "broken, faulty, or otherwise not working in this email?"
                    ),
                    criteria=[
                        "No product is described as defective.",
                        "Exactly one distinct product is described as defective.",
                        "Exactly two distinct products are described as defective.",
                        "Exactly three distinct products are described as defective.",
                        "Four or more distinct products are described as defective.",
                    ],
                ),
                **_date_questions(today),
            },
        )

    answers = response.answers
    delivery_date = _assemble_delivery_date(answers, today)

    return {
        "defective_product_count": round(answers["defective_count"].score),
        "defective_product_count_confidence": answers["defective_count"].confidence,
        "promised_delivery_date": delivery_date,
        "delivery_promise_passed": delivery_date is not None and delivery_date < today,
    }
