"""Read a customer email with TypeSafe's Jev model.

Reports how many distinct products the customer says are defective, and whether
the delivery date they were promised has already passed.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from typesafe_sdk import Choice, Score, TypeSafeClient

MODEL = "jev-latest"

# A date under this confidence (or one code can't assemble at all) is unreliable
# enough that callers should treat delivery_date_passed as unknown rather than act on it.
REVIEW_BELOW = 0.60

MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
YEAR_WINDOW = list(range(1900, 2051))

DEFECTIVE_PRODUCT_COUNT_LEVELS = [
    "The customer does not describe any product as defective, broken, damaged, or otherwise not working.",
    "The customer describes exactly one product as defective, broken, damaged, or otherwise not working.",
    "The customer describes exactly two distinct products as defective, broken, damaged, or otherwise not working.",
    "The customer describes exactly three distinct products as defective, broken, damaged, or otherwise not working.",
    "The customer describes four or more distinct products as defective, broken, damaged, or otherwise not working.",
]

DELIVERY_DATE_ROLE = "the delivery date the company promised the customer"


def _date_questions(role: str) -> dict[str, Choice]:
    """Seven typed choices that read a date's shape and parts off the text -- no math."""
    absent = "The document does not state this, or it is not this kind of date."
    return {
        "mode": Choice(
            instructions=(
                f"How is {role} written? 'absolute' = a calendar date naming a month (e.g. "
                "'August 14', 'the 3rd of March'); 'relative' = given relative to today (today, "
                "tomorrow, the day after tomorrow, or a named weekday such as 'next Thursday'); "
                "'none' = the document does not state this date."
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
                f"If {role} is an absolute calendar date, which year? Pick 'none' if the document "
                "states no year (code infers it), or 'out_of_range' if a year is stated but not "
                "in the list."
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
                f"If {role} names a weekday, which week is it in? 'next' for 'next Thursday' or "
                "'Thursday next week'; 'current' for 'this Thursday'; 'none' for a bare weekday "
                "with no qualifier (just 'Thursday' / 'on Thursday')."
            ),
            criteria={"current": None, "next": None, "none": absent},
        ),
    }


def _resolve_weekday(today: date, weekday: str, week_offset: str) -> date:
    """Which date a named weekday points to: a bare weekday is the next occurrence on or
    after today; 'next' is the following calendar week; 'current' is this week."""
    w = WEEKDAYS.index(weekday)
    this_monday = today - timedelta(days=today.weekday())
    if week_offset == "next":
        return this_monday + timedelta(days=7 + w)
    if week_offset == "current":
        return this_monday + timedelta(days=w)
    return today + timedelta(days=(w - today.weekday()) % 7)


def _assemble_date(parts: dict[str, dict[str, Any]], today: date) -> dict[str, Any]:
    """Resolve the parts Jev read into a concrete date. Confidence is the weakest of the
    parts the shape actually used."""
    mode = parts["mode"]["choice"]
    confs = [parts["mode"]["confidence"]]

    def result(resolved: date | None, note: str) -> dict[str, Any]:
        confidence = min(confs) if confs else None
        needs_review = resolved is None or confidence is None or confidence < REVIEW_BELOW
        return {"date": resolved, "confidence": confidence, "needs_review": needs_review, "note": note}

    if mode == "none":
        return result(None, "no such date stated")

    if mode == "absolute":
        month, day, year = parts["month"]["choice"], parts["day"]["choice"], parts["year"]["choice"]
        confs += [parts["month"]["confidence"], parts["day"]["confidence"], parts["year"]["confidence"]]
        if "none" in (month, day) or not day.isdigit() or month not in MONTHS:
            return result(None, "absolute date incomplete")
        if year == "out_of_range":
            return result(None, f"year outside {YEAR_WINDOW[0]}-{YEAR_WINDOW[-1]}")
        if year == "none":
            try:
                resolved = date(today.year, MONTHS[month], int(day))
            except ValueError:
                return result(None, f"impossible date: {month} {day}")
            if resolved < today - timedelta(days=31):
                resolved = date(today.year + 1, MONTHS[month], int(day))
            return result(resolved, "")
        try:
            return result(date(int(year), MONTHS[month], int(day)), "")
        except ValueError:
            return result(None, f"impossible date: {year}-{month}-{day}")

    if mode == "relative":
        anchor = parts["day_anchor"]["choice"]
        confs.append(parts["day_anchor"]["confidence"])
        if anchor == "today":
            return result(today, "")
        if anchor == "tomorrow":
            return result(today + timedelta(days=1), "")
        if anchor == "day_after":
            return result(today + timedelta(days=2), "")
        if anchor == "weekday":
            weekday, offset = parts["weekday"]["choice"], parts["week_offset"]["choice"]
            confs += [parts["weekday"]["confidence"], parts["week_offset"]["confidence"]]
            if weekday not in WEEKDAYS:
                return result(None, "relative weekday not read")
            return result(_resolve_weekday(today, weekday, offset), "")
        return result(None, "relative day not read")

    return result(None, f"unrecognized mode: {mode}")


def check_email(email_text: str, today: date) -> dict[str, Any]:
    """Ask Jev about a customer email in one call and resolve the answers in code.

    Returns a dict with:
      - defective_product_count: int, the number of distinct products (capped display
        at 4, meaning "4 or more") the customer describes as defective.
      - defective_product_count_confidence: float, Jev's confidence in that count.
      - delivery_date: date | None, the promised delivery date, or None if the email
        never states one.
      - delivery_date_passed: bool | None, whether delivery_date is before `today`;
        None when no delivery date could be determined.
      - needs_review: bool, True when either judgment is too uncertain to act on
        automatically (see REVIEW_BELOW).
    """
    questions = {
        "defective_product_count": Score(
            instructions=(
                "How many distinct products does the customer describe as defective, "
                "broken, damaged, or otherwise not working?"
            ),
            criteria=DEFECTIVE_PRODUCT_COUNT_LEVELS,
        ),
        **_date_questions(DELIVERY_DATE_ROLE),
    }

    with TypeSafeClient() as client:
        response = client.system_one(state=email_text, questions=questions, model=MODEL)

    count_answer = response.scores["defective_product_count"]
    date_parts = {
        name: {"choice": response.choices[name].choice, "confidence": response.choices[name].confidence}
        for name in ("mode", "month", "day", "year", "day_anchor", "weekday", "week_offset")
    }
    delivery = _assemble_date(date_parts, today)

    return {
        "defective_product_count": round(count_answer.score),
        "defective_product_count_confidence": count_answer.confidence,
        "delivery_date": delivery["date"],
        "delivery_date_passed": delivery["date"] < today if delivery["date"] is not None else None,
        "needs_review": delivery["needs_review"] or count_answer.confidence < REVIEW_BELOW,
    }
