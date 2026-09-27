"""Read a customer email with TypeSafe's Jev model and report the number of
distinct defective products the customer mentions, and whether the delivery
date the company promised them has already passed.

Jev never counts or does date math itself (see docs.typesafe.ai/model-jaggedness).
Both facts are assembled here from narrow per-sentence/per-part judgments:
counting is a Noul "is this a new one?" per sentence, summed in code; the date
is built from Jev's extracted parts (mode/month/day/year or a relative anchor)
using ``today``, following the docs' date_extraction_cookbook.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Optional

from typesafe_sdk import Choice, Noul, NoulCriteria, TypeSafeClient

MODEL = "jev-1.13.0"

DEFECT_THRESHOLD = 0.5
DISTINCT_THRESHOLD = 0.5
DATE_REVIEW_BELOW = 0.60

_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
_MONTH_TO_NUM = {name: i + 1 for i, name in enumerate(_MONTHS)}

_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_WEEKDAY_TO_NUM = {name: i for i, name in enumerate(_WEEKDAYS)}

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(text.strip()) if s.strip()]


def _resolve_weekday(today: date, target_weekday: int, week_offset: str) -> date:
    days_ahead = (target_weekday - today.weekday()) % 7
    if week_offset == "current":
        monday = today - timedelta(days=today.weekday())
        return monday + timedelta(days=target_weekday)
    if week_offset == "next":
        next_monday = today - timedelta(days=today.weekday()) + timedelta(days=7)
        return next_monday + timedelta(days=target_weekday)
    # A bare weekday ("none" offset) means the next occurrence on or after today.
    return today + timedelta(days=days_ahead)


def _assemble_delivery_date(choices: dict, today: date) -> tuple[Optional[date], float, bool]:
    mode = choices["mode"]
    if mode.choice == "none":
        return None, mode.confidence, mode.confidence < DATE_REVIEW_BELOW

    if mode.choice == "absolute":
        month_ans, day_ans, year_ans = choices["month"], choices["day"], choices["year"]
        confidences = [mode.confidence, month_ans.confidence, day_ans.confidence]
        month = _MONTH_TO_NUM.get(month_ans.choice)
        day = int(day_ans.choice) if day_ans.choice != "none" else None
        if month is None or day is None:
            return None, min(confidences), True

        if year_ans.choice == "out_of_range":
            return None, min(confidences + [year_ans.confidence]), True
        if year_ans.choice == "none":
            confidences.append(year_ans.confidence)
            try:
                candidate = date(today.year, month, day)
            except ValueError:
                return None, min(confidences), True
            # An unstated year that reads over a month in the past means "next year".
            if (candidate - today).days < -31:
                try:
                    candidate = date(today.year + 1, month, day)
                except ValueError:
                    return None, min(confidences), True
        else:
            confidences.append(year_ans.confidence)
            try:
                candidate = date(int(year_ans.choice), month, day)
            except ValueError:
                return None, min(confidences), True
        return candidate, min(confidences), False

    if mode.choice == "relative":
        anchor_ans = choices["day_anchor"]
        confidences = [mode.confidence, anchor_ans.confidence]
        if anchor_ans.choice == "today":
            return today, min(confidences), False
        if anchor_ans.choice == "tomorrow":
            return today + timedelta(days=1), min(confidences), False
        if anchor_ans.choice == "day_after":
            return today + timedelta(days=2), min(confidences), False
        if anchor_ans.choice == "weekday":
            weekday_ans, offset_ans = choices["weekday"], choices["week_offset"]
            confidences += [weekday_ans.confidence, offset_ans.confidence]
            target_weekday = _WEEKDAY_TO_NUM.get(weekday_ans.choice)
            if target_weekday is None:
                return None, min(confidences), True
            resolved = _resolve_weekday(today, target_weekday, offset_ans.choice)
            return resolved, min(confidences), False
        return None, min(confidences), True

    return None, mode.confidence, True


def _build_date_questions(today: date) -> dict[str, Choice]:
    return {
        "mode": Choice(
            instructions=(
                "How is the delivery date the company promised the customer written in `email`? "
                "'absolute' names a calendar date (a month, or a month and day). "
                "'relative' is phrased relative to today (e.g. 'tomorrow', 'next Friday', 'in two days'). "
                "'none' if no promised delivery date is stated."
            ),
            criteria={"absolute": None, "relative": None, "none": "No promised delivery date is stated in `email`."},
        ),
        "month": Choice(
            instructions="If the promised delivery date in `email` is an absolute calendar date, which month?",
            criteria={m: None for m in _MONTHS} | {"none": "The date is not absolute, or no month is stated."},
        ),
        "day": Choice(
            instructions=(
                "If the promised delivery date in `email` is an absolute calendar date, "
                "which day of the month (1-31)?"
            ),
            criteria={str(d): None for d in range(1, 32)}
            | {"none": "The date is not absolute, or no day of month is stated."},
        ),
        "year": Choice(
            instructions="If the promised delivery date in `email` is an absolute calendar date, which year?",
            criteria={str(y): None for y in range(today.year - 1, today.year + 3)}
            | {
                "out_of_range": "A year is stated but falls outside the listed range.",
                "none": "The date is not absolute, or no year is stated.",
            },
        ),
        "day_anchor": Choice(
            instructions=(
                "If the promised delivery date in `email` is relative to today, which does it name? "
                "'today', 'tomorrow', 'day_after' (the day after tomorrow), or 'weekday' (a named day of the week)."
            ),
            criteria={
                "today": None,
                "tomorrow": None,
                "day_after": None,
                "weekday": None,
                "none": "The date is not relative.",
            },
        ),
        "weekday": Choice(
            instructions="If the promised delivery date in `email` names a day of the week, which one?",
            criteria={w: None for w in _WEEKDAYS} | {"none": "No day of the week is named."},
        ),
        "week_offset": Choice(
            instructions=(
                "If the promised delivery date in `email` names a day of the week, is it this "
                "('current') calendar week, the following ('next') week, or is the week unspecified "
                "(a bare day name, 'none')?"
            ),
            criteria={
                "current": None,
                "next": None,
                "none": "No day of the week is named, or the week is unspecified.",
            },
        ),
    }


def _build_defect_questions(sentences: list[str]) -> dict[str, Noul]:
    questions: dict[str, Noul] = {}
    for i in range(len(sentences)):
        questions[f"defect_{i}"] = Noul(
            instructions=(
                f"Does `sentences[{i}]` say that a specific product the customer bought is defective, "
                "broken, damaged, faulty, or otherwise not working as expected? Complaints about "
                "shipping, billing, or customer service alone do not count."
            ),
            criteria=NoulCriteria(
                true="Names or clearly refers to a product and says it is faulty in some way.",
                false="No product is called faulty, or the sentence complains about something else.",
            ),
        )
        if i > 0:
            questions[f"distinct_{i}"] = Noul(
                instructions=(
                    f"Is the product named in `sentences[{i}]` a different product from every product "
                    f"named in `sentences[0]` through `sentences[{i - 1}]`? Answer yes if `sentences[{i}]` "
                    "does not name a defective product, or if it names one not already covered earlier."
                ),
            )
    return questions


def check_email(email_text: str, today: date) -> dict:
    """Report the distinct defective-product count and whether the promised
    delivery date in ``email_text`` has passed, relative to ``today``."""
    sentences = _split_sentences(email_text)
    if not sentences:
        return {
            "defective_product_count": 0,
            "promised_delivery_date": None,
            "delivery_date_passed": None,
            "delivery_date_confidence": None,
            "needs_review": False,
            "model": None,
        }

    state = {"email": email_text, "sentences": sentences}
    questions: dict[str, object] = {
        **_build_date_questions(today),
        **_build_defect_questions(sentences),
    }

    with TypeSafeClient() as client:
        response = client.system_one(state=state, questions=questions, model=MODEL)

    defective_product_count = 0
    for i in range(len(sentences)):
        if response.nouls[f"defect_{i}"].noul < DEFECT_THRESHOLD:
            continue
        if i == 0 or response.nouls[f"distinct_{i}"].noul >= DISTINCT_THRESHOLD:
            defective_product_count += 1

    delivery_date, date_confidence, date_needs_review = _assemble_delivery_date(response.choices, today)

    return {
        "defective_product_count": defective_product_count,
        "promised_delivery_date": delivery_date.isoformat() if delivery_date else None,
        "delivery_date_passed": (delivery_date < today) if delivery_date else None,
        "delivery_date_confidence": date_confidence,
        "needs_review": date_needs_review,
        "model": response.model,
    }
