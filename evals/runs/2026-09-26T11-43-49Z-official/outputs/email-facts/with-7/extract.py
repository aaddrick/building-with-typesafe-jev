"""Extract defect and delivery-date facts from a customer email using Jev."""

from datetime import date, timedelta

from typesafe_sdk import Choice, TypeSafeClient

_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_REVIEW_THRESHOLD = 0.6


def _defect_count_question() -> dict[str, Choice]:
    return {
        "defect_count": Choice(
            instructions=(
                "How many different products does the customer say are defective, "
                "damaged, broken, or otherwise not working in this email? Count "
                "each distinct product once even if it is mentioned more than once."
            ),
            criteria={
                "0": "No product is described as defective.",
                "1": "Exactly one distinct product is described as defective.",
                "2": "Exactly two distinct products are described as defective.",
                "3": "Exactly three distinct products are described as defective.",
                "4": "Exactly four distinct products are described as defective.",
                "5_or_more": "Five or more distinct products are described as defective.",
            },
        )
    }


def _delivery_date_questions() -> dict[str, Choice]:
    role = "the delivery date the company promised the customer"
    return {
        "delivery_mode": Choice(
            instructions=(
                f"Is {role} absolute (names a month/day), relative (e.g. today, "
                "tomorrow, a weekday), or not stated at all?"
            ),
            criteria={"absolute": None, "relative": None, "none": "Not stated in the email."},
        ),
        "delivery_month": Choice(
            instructions=f"Which month is named for {role}?",
            criteria={m: None for m in _MONTHS} | {"none": "Not stated or not absolute."},
        ),
        "delivery_day": Choice(
            instructions=f"Which day of the month (1-31) is named for {role}?",
            criteria={str(d): None for d in range(1, 32)} | {"none": "Not stated or not absolute."},
        ),
        "delivery_year": Choice(
            instructions=f"Which year is named for {role}, if any?",
            criteria={str(y): None for y in range(2020, 2036)} | {"none": "Not stated; infer from context."},
        ),
        "delivery_day_anchor": Choice(
            instructions=(
                f"If {role} is relative, is it today, tomorrow, the day after "
                "tomorrow, or a named weekday?"
            ),
            criteria={
                "today": None,
                "tomorrow": None,
                "day_after": None,
                "weekday": None,
                "none": "Not stated or not relative.",
            },
        ),
        "delivery_weekday": Choice(
            instructions=f"If {role} names a weekday, which one?",
            criteria={d: None for d in _WEEKDAYS} | {"none": "Not applicable."},
        ),
        "delivery_week_offset": Choice(
            instructions=f"If {role} names a weekday, is it this current week or next week?",
            criteria={"current": None, "next": None, "none": "Not applicable."},
        ),
    }


def _resolve_weekday(today: date, weekday: str, week_offset: str) -> date:
    target = _WEEKDAYS.index(weekday)
    this_monday = today - timedelta(days=today.weekday())
    if week_offset == "next":
        return this_monday + timedelta(days=7 + target)
    if week_offset == "current":
        return this_monday + timedelta(days=target)
    return today + timedelta(days=(target - today.weekday()) % 7)


def _resolve_delivery_date(choices: dict, today: date) -> tuple[date | None, float]:
    mode = choices["delivery_mode"]
    confidences = [mode.confidence]

    if mode.choice == "none":
        return None, mode.confidence

    if mode.choice == "absolute":
        month_ans, day_ans, year_ans = (
            choices["delivery_month"], choices["delivery_day"], choices["delivery_year"]
        )
        confidences += [month_ans.confidence, day_ans.confidence, year_ans.confidence]
        month_index = {m: i + 1 for i, m in enumerate(_MONTHS)}.get(month_ans.choice)
        if month_index is None or not day_ans.choice.isdigit():
            return None, min(confidences)
        day = int(day_ans.choice)
        try:
            if year_ans.choice == "none":
                resolved = date(today.year, month_index, day)
                if resolved < today - timedelta(days=31):
                    resolved = date(today.year + 1, month_index, day)
            else:
                resolved = date(int(year_ans.choice), month_index, day)
        except ValueError:
            return None, min(confidences)
        return resolved, min(confidences)

    if mode.choice == "relative":
        anchor = choices["delivery_day_anchor"]
        confidences.append(anchor.confidence)
        if anchor.choice == "today":
            resolved = today
        elif anchor.choice == "tomorrow":
            resolved = today + timedelta(days=1)
        elif anchor.choice == "day_after":
            resolved = today + timedelta(days=2)
        elif anchor.choice == "weekday":
            weekday_ans, offset_ans = choices["delivery_weekday"], choices["delivery_week_offset"]
            confidences += [weekday_ans.confidence, offset_ans.confidence]
            if weekday_ans.choice == "none":
                return None, min(confidences)
            resolved = _resolve_weekday(today, weekday_ans.choice, offset_ans.choice)
        else:
            return None, min(confidences)
        return resolved, min(confidences)

    return None, min(confidences)


def check_email(email_text: str, today: date) -> dict:
    """Report how many distinct products a customer says are defective, and
    whether the delivery date they were promised has already passed."""
    client = TypeSafeClient()
    questions = {**_defect_count_question(), **_delivery_date_questions()}
    response = client.system_one(state={"email_body": email_text}, questions=questions)
    choices = response.choices

    defect_answer = choices["defect_count"]
    defective_product_count = (
        5 if defect_answer.choice == "5_or_more" else int(defect_answer.choice)
    )

    promised_delivery_date, delivery_date_confidence = _resolve_delivery_date(choices, today)
    delivery_already_passed = (
        promised_delivery_date < today if promised_delivery_date is not None else None
    )

    needs_review = (
        defect_answer.confidence < _REVIEW_THRESHOLD
        or promised_delivery_date is None
        or delivery_date_confidence < _REVIEW_THRESHOLD
    )

    return {
        "defective_product_count": defective_product_count,
        "defective_product_count_confidence": defect_answer.confidence,
        "promised_delivery_date": promised_delivery_date,
        "delivery_date_confidence": delivery_date_confidence,
        "delivery_already_passed": delivery_already_passed,
        "needs_review": needs_review,
    }
