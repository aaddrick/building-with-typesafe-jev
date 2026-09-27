"""Read a customer email with TypeSafe's Jev model.

Two judgments are combined:
- how many distinct products the customer reports as defective (a Score,
  bucketed into situational levels since Jev cannot enumerate an open-ended
  list of product names it was never given as candidates)
- what delivery date, if any, was promised, resolved to a concrete date in
  code and compared against `today` (the pattern from TypeSafe's date
  extraction cookbook: read the date's parts with Jev, assemble in code)
"""

import datetime

from typesafe_sdk import Choice, Score, TypeSafeClient

TYPESAFE_MODEL = "jev-latest"

_MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11,
    "December": 12,
}
_WEEKDAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
]
_YEARS = [str(y) for y in range(1900, 2101)]

_DATE_ABSENT = "The email does not promise a delivery date, or this part cannot be read from it."

_DELIVERY_DATE_QUESTIONS = {
    "delivery_date_mode": Choice(
        instructions=(
            "How is the delivery date the company promised the customer written? "
            "'absolute' = a calendar date naming a month; 'relative' = stated "
            "relative to today (e.g. 'tomorrow', 'next Tuesday'); 'none' = no "
            "delivery date is promised in this email."
        ),
        criteria={"absolute": None, "relative": None, "none": None},
    ),
    "delivery_date_month": Choice(
        instructions="If the promised delivery date is absolute, which month?",
        criteria={m: None for m in _MONTHS} | {"none": _DATE_ABSENT},
    ),
    "delivery_date_day": Choice(
        instructions="If the promised delivery date is absolute, which day of the month (1-31)?",
        criteria={str(d): None for d in range(1, 32)} | {"none": _DATE_ABSENT},
    ),
    "delivery_date_year": Choice(
        instructions=(
            "If the promised delivery date is absolute, which year? 'none' if "
            "unstated, 'out_of_range' if outside 1900-2100."
        ),
        criteria={y: None for y in _YEARS} | {
            "out_of_range": "Year stated but outside 1900-2100.",
            "none": "No year stated.",
        },
    ),
    "delivery_date_anchor": Choice(
        instructions=(
            "If the promised delivery date is relative, which day? 'today', "
            "'tomorrow', 'day_after' (day after tomorrow), or 'weekday' (a named "
            "day of the week)."
        ),
        criteria={
            "today": None, "tomorrow": None, "day_after": None, "weekday": None,
            "none": _DATE_ABSENT,
        },
    ),
    "delivery_date_weekday": Choice(
        instructions="If the promised delivery date names a weekday, which one?",
        criteria={w: None for w in _WEEKDAYS} | {"none": _DATE_ABSENT},
    ),
    "delivery_date_week_offset": Choice(
        instructions=(
            "If the promised delivery date names a weekday, is it this current "
            "week or next week? 'none' if unqualified or not applicable."
        ),
        criteria={"current": None, "next": None, "none": _DATE_ABSENT},
    ),
}

_PRODUCT_COUNT_QUESTION = {
    "defective_product_count": Score(
        instructions=(
            "How many different products does the customer report as "
            "defective, broken, faulty, or otherwise not working, in this "
            "email? Count each distinct product once, even if it is mentioned "
            "more than once."
        ),
        criteria=[
            {
                "what": "No product is described as defective, broken, or faulty.",
                "examples": [
                    "the email only asks about an order's shipping status",
                    "the email is a general compliment or unrelated question",
                ],
            },
            {
                "what": "Exactly one distinct product is described as defective, broken, or faulty.",
                "examples": ["the customer says the blender they ordered does not turn on"],
            },
            {
                "what": "Exactly two distinct products are described as defective, broken, or faulty.",
                "examples": ["the customer says both the toaster and the kettle arrived broken"],
            },
            {
                "what": "Three or more distinct products are described as defective, broken, or faulty.",
                "examples": ["the customer lists a phone, a case, and a charger as all broken"],
            },
        ],
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


def _resolve_delivery_date(choices, today: datetime.date):
    """Assemble the parts Jev read into a concrete date, or None if unreadable."""
    mode = choices["delivery_date_mode"]
    confidences = [mode.confidence]

    def done(resolved, extra_confidences=()):
        used = [c for c in (*confidences, *extra_confidences) if c is not None]
        return resolved, (min(used) if used else None)

    if mode.choice == "none":
        return done(None)

    if mode.choice == "absolute":
        month_ans = choices["delivery_date_month"]
        day_ans = choices["delivery_date_day"]
        year_ans = choices["delivery_date_year"]
        confidences += [month_ans.confidence, day_ans.confidence, year_ans.confidence]
        month, day, year = month_ans.choice, day_ans.choice, year_ans.choice

        if month == "none" or day == "none" or month not in _MONTHS or year == "out_of_range":
            return done(None)

        try:
            if year == "none":
                resolved = datetime.date(today.year, _MONTHS[month], int(day))
                if resolved < today - datetime.timedelta(days=31):
                    resolved = datetime.date(today.year + 1, _MONTHS[month], int(day))
            else:
                resolved = datetime.date(int(year), _MONTHS[month], int(day))
        except ValueError:
            return done(None)

        return done(resolved)

    if mode.choice == "relative":
        anchor_ans = choices["delivery_date_anchor"]
        confidences.append(anchor_ans.confidence)
        anchor = anchor_ans.choice

        if anchor == "today":
            return done(today)
        if anchor == "tomorrow":
            return done(today + datetime.timedelta(days=1))
        if anchor == "day_after":
            return done(today + datetime.timedelta(days=2))
        if anchor == "weekday":
            weekday_ans = choices["delivery_date_weekday"]
            offset_ans = choices["delivery_date_week_offset"]
            confidences += [weekday_ans.confidence, offset_ans.confidence]
            if weekday_ans.choice not in _WEEKDAYS:
                return done(None)
            return done(_resolve_weekday(today, weekday_ans.choice, offset_ans.choice))

    return done(None)


def _mode_count(score_answer) -> int:
    """Most probable bucket, as an int (the top bucket means '3 or more')."""
    best_level = max(score_answer.probabilities, key=score_answer.probabilities.get)
    return int(best_level)


def check_email(email_text: str, today: datetime.date) -> dict:
    with TypeSafeClient() as client:
        response = client.system_one(
            state=email_text,
            questions={**_DELIVERY_DATE_QUESTIONS, **_PRODUCT_COUNT_QUESTION},
            model=TYPESAFE_MODEL,
        )

    delivery_date, delivery_date_confidence = _resolve_delivery_date(response.choices, today)
    count_answer = response.scores["defective_product_count"]

    return {
        "defective_product_count": _mode_count(count_answer),
        "defective_product_count_confidence": count_answer.confidence,
        "promised_delivery_date": delivery_date,
        "promised_delivery_date_confidence": delivery_date_confidence,
        "delivery_already_passed": (
            None if delivery_date is None else delivery_date < today
        ),
    }
