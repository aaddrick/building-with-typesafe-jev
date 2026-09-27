import datetime

from typesafe_sdk import Choice, Noul, TypeSafeClient

CONFIDENCE_THRESHOLD = 0.60

MONTHS = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

_DEFECT_COUNT_VALUES = {"0": 0, "1": 1, "2": 2, "3": 3, "4_or_more": 4}


def _build_questions() -> dict:
    return {
        "defective_product_count": Choice(
            instructions=(
                "How many different products does the customer describe as defective, "
                "broken, damaged, or otherwise not working as expected? Count each "
                "distinct product only once, even if it is mentioned more than once."
            ),
            criteria={
                "0": "No product is described as defective.",
                "1": "Exactly one distinct product is described as defective.",
                "2": "Exactly two distinct products are described as defective.",
                "3": "Exactly three distinct products are described as defective.",
                "4_or_more": "Four or more distinct products are described as defective.",
            },
        ),
        "delivery_mentioned": Noul(
            instructions=(
                "The email states or implies a specific delivery date that was promised "
                "to the customer, e.g. 'arriving by Friday', 'expected March 3rd', or "
                "'within 2 business days'."
            ),
        ),
        "date_mode": Choice(
            instructions=(
                "If the email promises a delivery date, is it stated as an absolute "
                "calendar date (names a specific month and day) or a relative date "
                "(tied to today, like 'tomorrow' or 'next Friday')? Choose 'unstated' "
                "if no delivery date is promised or none can be determined."
            ),
            criteria={
                "absolute": "A specific month and day are named.",
                "relative": "The date is expressed relative to today, not a named month/day.",
                "unstated": "No promised delivery date is present.",
            },
        ),
        "month": Choice(
            instructions=(
                "If the promised delivery date is an absolute calendar date, which "
                "month was named? Choose 'unstated' if not applicable."
            ),
            criteria={**{m: None for m in MONTHS}, "unstated": "No month was named."},
        ),
        "day": Choice(
            instructions=(
                "If the promised delivery date is an absolute calendar date, which day "
                "of the month was named? Choose 'unstated' if not applicable."
            ),
            criteria={**{str(d): None for d in range(1, 32)}, "unstated": "No day was named."},
        ),
        "day_anchor": Choice(
            instructions=(
                "If the promised delivery date is relative to today, how is it expressed?"
            ),
            criteria={
                "today": "The delivery is promised for today.",
                "tomorrow": "The delivery is promised for tomorrow.",
                "day_after_tomorrow": "The delivery is promised for the day after tomorrow.",
                "weekday": "The delivery is promised for a specific named day of the week.",
                "unstated": "Not applicable.",
            },
        ),
        "weekday": Choice(
            instructions=(
                "If the relative delivery date refers to a specific day of the week "
                "(e.g. 'Friday'), which weekday is named? Choose 'unstated' if not applicable."
            ),
            criteria={**{w: None for w in WEEKDAYS}, "unstated": "No weekday was named."},
        ),
        "week_offset": Choice(
            instructions=(
                "If a weekday is named for the relative delivery date, is it qualified "
                "as 'this week', 'next week', or given with no qualifier at all "
                "(e.g. bare 'Friday')?"
            ),
            criteria={
                "current": "Explicitly qualified as this/the current week.",
                "next": "Explicitly qualified as next week.",
                "unqualified": "No week qualifier was given.",
                "unstated": "Not applicable.",
            },
        ),
    }


def _resolve_absolute_date(month_name: str, day_str: str, today: datetime.date):
    if month_name == "unstated" or day_str == "unstated":
        return None
    month = MONTHS.index(month_name) + 1
    day = int(day_str)
    try:
        candidate = datetime.date(today.year, month, day)
    except ValueError:
        return None
    # No year is ever extracted from the text (Jev never does calendar math), so a
    # date that already looks more than a month stale is assumed to mean next year.
    if (today - candidate).days > 31:
        try:
            candidate = datetime.date(today.year + 1, month, day)
        except ValueError:
            return None
    return candidate


def _resolve_weekday_date(weekday_name: str, week_offset: str, today: datetime.date):
    if weekday_name == "unstated":
        return None
    target = WEEKDAYS.index(weekday_name)
    week_start = today - datetime.timedelta(days=today.weekday())
    if week_offset == "next":
        return week_start + datetime.timedelta(days=7 + target)
    if week_offset == "current":
        return week_start + datetime.timedelta(days=target)
    # "unqualified" (bare weekday) or "unstated": next occurrence on or after today.
    days_ahead = (target - today.weekday()) % 7
    return today + datetime.timedelta(days=days_ahead)


def _resolve_delivery_date(answers: dict, today: datetime.date):
    if answers["delivery_mentioned"].noul < 0.5:
        return None, None

    mode_answer = answers["date_mode"]
    if mode_answer.choice == "absolute":
        month_answer, day_answer = answers["month"], answers["day"]
        resolved = _resolve_absolute_date(month_answer.choice, day_answer.choice, today)
        confidence = min(mode_answer.confidence, month_answer.confidence, day_answer.confidence)
    elif mode_answer.choice == "relative":
        anchor_answer = answers["day_anchor"]
        confidences = [mode_answer.confidence, anchor_answer.confidence]
        if anchor_answer.choice == "weekday":
            weekday_answer, offset_answer = answers["weekday"], answers["week_offset"]
            resolved = _resolve_weekday_date(weekday_answer.choice, offset_answer.choice, today)
            confidences += [weekday_answer.confidence, offset_answer.confidence]
        elif anchor_answer.choice in ("today", "tomorrow", "day_after_tomorrow"):
            offset = {"today": 0, "tomorrow": 1, "day_after_tomorrow": 2}[anchor_answer.choice]
            resolved = today + datetime.timedelta(days=offset)
        else:
            resolved = None
        confidence = min(confidences)
    else:
        return None, None

    return resolved, confidence


def check_email(email_text: str, today: datetime.date) -> dict:
    with TypeSafeClient() as client:
        response = client.system_one(state=email_text, questions=_build_questions())
    answers = response.answers

    defect_answer = answers["defective_product_count"]
    defect_count = _DEFECT_COUNT_VALUES[defect_answer.choice]

    delivery_date, date_confidence = _resolve_delivery_date(answers, today)
    delivery_promised = answers["delivery_mentioned"].noul >= 0.5

    return {
        "defective_product_count": defect_count,
        "defective_product_count_confidence": defect_answer.confidence,
        "promised_delivery_date": delivery_date,
        "delivery_date_confidence": date_confidence,
        "delivery_date_passed": (delivery_date < today) if delivery_date else None,
        "needs_review": (
            defect_answer.confidence < CONFIDENCE_THRESHOLD
            or (date_confidence is not None and date_confidence < CONFIDENCE_THRESHOLD)
            or (delivery_promised and delivery_date is None)
        ),
    }
