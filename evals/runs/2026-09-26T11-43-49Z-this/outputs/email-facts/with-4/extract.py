"""Extract customer-email facts (defective product count, delivery date status) via Jev.

Counting and date arithmetic stay in code (Jev is bad at both); Jev only supplies
per-sentence judgments and date-part extraction. See docs.typesafe.ai for the
System One / Choice / Noul primitives this relies on.
"""

from __future__ import annotations

import datetime
import re

from typesafe_sdk import Choice, Noul, TypeSafeClient

MODEL = "jev-1.13.0"  # pinned: thresholds below are tuned against this version

DEFECT_MENTION_THRESHOLD = 0.5
NEW_PRODUCT_THRESHOLD = 0.5
DATE_REVIEW_BELOW = 0.60  # per the date_extraction cookbook

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

_client: TypeSafeClient | None = None


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        _client = TypeSafeClient()
    return _client


def _split_sentences(email_text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(email_text.strip()) if s.strip()]


def _defect_questions(sentences: list[str]) -> dict[str, Noul]:
    """One Noul per sentence for "is this a defect mention", plus a dedupe Noul
    against every earlier sentence, per the distinct-item-counting recipe."""
    questions: dict[str, Noul] = {}
    for i in range(len(sentences)):
        questions[f"defect_mention_{i}"] = Noul(
            instructions=(
                f"Does `sentences[{i}]` state that a specific product the customer "
                "received is defective, broken, faulty, damaged, or not working?"
            ),
        )
        if i > 0:
            questions[f"new_product_{i}"] = Noul(
                instructions=(
                    f"If `sentences[{i}]` describes a defective product, is that "
                    f"product different from every product already described as "
                    f"defective in `sentences[0]` through `sentences[{i - 1}]`?"
                ),
            )
    return questions


def _date_questions() -> dict[str, Choice]:
    """Seven Choices that extract date parts; code assembles and compares them."""
    return {
        "date_mode": Choice(
            instructions=(
                "How is the delivery date that was promised to the customer for "
                "their order expressed in `email_text`? `absolute` = a specific "
                "calendar date or month/day (with or without a year). `relative` "
                "= expressed relative to today, such as a weekday name, "
                "'tomorrow', or 'in N days'. `none` = no delivery date was "
                "promised or mentioned."
            ),
            criteria={"absolute": None, "relative": None, "none": None},
        ),
        "date_month": Choice(
            instructions=(
                "If a promised delivery date is stated with a calendar month, "
                "which month? `none` if no month is stated."
            ),
            criteria={m: None for m in MONTHS} | {"none": None},
        ),
        "date_day": Choice(
            instructions=(
                "If a promised delivery date is stated with a day of the month, "
                "which day number? `none` if no day is stated."
            ),
            criteria={str(d): None for d in range(1, 32)} | {"none": None},
        ),
        "date_year": Choice(
            instructions=(
                "If a promised delivery date is stated with a year, which year? "
                "`none` if no year is stated, `out_of_range` if a year is stated "
                "but outside 1900-2050."
            ),
            criteria={str(y): None for y in range(1900, 2051)} | {
                "out_of_range": "A year is stated but is before 1900 or after 2050.",
                "none": "No year is stated.",
            },
        ),
        "date_day_anchor": Choice(
            instructions=(
                "If the promised delivery date is relative to today, what is it "
                "anchored to? `today`, `tomorrow`, `day_after` (the day after "
                "tomorrow), `weekday` (a named day of the week), or `none` if "
                "not relative or not stated."
            ),
            criteria={"today": None, "tomorrow": None, "day_after": None, "weekday": None, "none": None},
        ),
        "date_weekday": Choice(
            instructions=(
                "If the promised delivery date names a day of the week, which "
                "one? `none` if not stated."
            ),
            criteria={w: None for w in WEEKDAYS} | {"none": None},
        ),
        "date_week_offset": Choice(
            instructions=(
                "If the promised delivery date names a day of the week, is it "
                "qualified as `current` (this week) or `next` (next week)? "
                "`none` if unqualified (a bare weekday name) or not stated."
            ),
            criteria={"current": None, "next": None, "none": None},
        ),
    }


def _resolve_weekday(weekday: str, week_offset: str, today: datetime.date) -> datetime.date:
    target_idx = WEEKDAYS.index(weekday)
    today_idx = today.weekday()
    if week_offset == "next":
        next_monday = today + datetime.timedelta(days=7 - today_idx)
        return next_monday + datetime.timedelta(days=target_idx)
    if week_offset == "current":
        return today + datetime.timedelta(days=target_idx - today_idx)
    # bare weekday, no qualifier: next occurrence on or after today
    return today + datetime.timedelta(days=(target_idx - today_idx) % 7)


def _assemble_date(parts: dict[str, str], today: datetime.date) -> tuple[datetime.date | None, bool]:
    """Combine the extracted date parts into a date. Returns (date, assembly_failed)."""
    mode = parts["date_mode"]
    if mode == "none":
        return None, False

    if mode == "absolute":
        month, day, year = parts["date_month"], parts["date_day"], parts["date_year"]
        if month == "none" or day == "none" or year == "out_of_range":
            return None, True
        month_num = MONTHS.index(month) + 1
        day_num = int(day)
        year_inferred = year == "none"
        year_num = today.year if year_inferred else int(year)
        try:
            date = datetime.date(year_num, month_num, day_num)
        except ValueError:
            return None, True
        if year_inferred and (today - date).days > 31:
            date = date.replace(year=year_num + 1)
        return date, False

    if mode == "relative":
        anchor = parts["date_day_anchor"]
        if anchor == "today":
            return today, False
        if anchor == "tomorrow":
            return today + datetime.timedelta(days=1), False
        if anchor == "day_after":
            return today + datetime.timedelta(days=2), False
        if anchor == "weekday":
            weekday = parts["date_weekday"]
            if weekday == "none":
                return None, True
            return _resolve_weekday(weekday, parts["date_week_offset"], today), False
        return None, True

    return None, True


def check_email(email_text: str, today: datetime.date) -> dict:
    """Read a customer email and report defective-product count and delivery status.

    Returns a dict with:
      - defective_product_count: number of distinct products the customer says are defective
      - delivery_date: the promised delivery date, or None if not stated / not assembled
      - delivery_date_passed: True/False, or None if delivery_date is None
      - needs_review: True if the date extraction was low-confidence or inconsistent
      - model: the versioned Jev model that answered
    """
    sentences = _split_sentences(email_text)

    questions: dict[str, Choice | Noul] = {}
    questions.update(_defect_questions(sentences))
    questions.update(_date_questions())

    state = {"email_text": email_text, "sentences": sentences}
    response = _get_client().system_one(state=state, questions=questions, model=MODEL)

    defective_count = 0
    for i in range(len(sentences)):
        if response.nouls[f"defect_mention_{i}"].noul <= DEFECT_MENTION_THRESHOLD:
            continue
        if i == 0 or response.nouls[f"new_product_{i}"].noul > NEW_PRODUCT_THRESHOLD:
            defective_count += 1

    date_parts = {
        qid: response.choices[qid].choice
        for qid in (
            "date_mode", "date_month", "date_day", "date_year",
            "date_day_anchor", "date_weekday", "date_week_offset",
        )
    }
    delivery_date, assembly_failed = _assemble_date(date_parts, today)

    needs_review = assembly_failed
    if delivery_date is not None:
        if date_parts["date_mode"] == "absolute":
            used = ["date_mode", "date_month", "date_day", "date_year"]
        else:
            used = ["date_mode", "date_day_anchor"]
            if date_parts["date_day_anchor"] == "weekday":
                used += ["date_weekday", "date_week_offset"]
        min_confidence = min(response.choices[q].confidence for q in used)
        needs_review = needs_review or min_confidence < DATE_REVIEW_BELOW

    return {
        "defective_product_count": defective_count,
        "delivery_date": delivery_date,
        "delivery_date_passed": None if delivery_date is None else delivery_date < today,
        "needs_review": needs_review,
        "model": response.model,
    }
