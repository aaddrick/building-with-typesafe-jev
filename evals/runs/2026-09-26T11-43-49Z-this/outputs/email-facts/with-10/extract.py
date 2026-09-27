"""Read a customer email with typesafe.ai's Jev model.

Reports:
  - how many distinct products the customer says are defective
  - whether the delivery date the company promised has already passed

Jev never counts or does date math itself (see docs.typesafe.ai/concepts/system-one):
this module asks Jev only for atomic per-sentence judgments and structured date
parts, then does the counting and calendar arithmetic in plain Python.
"""

import calendar
import re
from datetime import date, timedelta
from typing import Optional

from typesafe_sdk import Choice, Noul, NoulCriteria, TypeSafeClient

# Pin the model version so the thresholds below stay valid if a newer
# `jev-latest` changes behavior.
MODEL = "jev-1.13.0"

# Tunable knobs, kept together per the skill's guidance to centralize
# thresholds that a human would want to review.
DEFECT_NOUL_THRESHOLD = 0.5
DISTINCT_NOUL_THRESHOLD = 0.5

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")

_client: Optional[TypeSafeClient] = None


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        _client = TypeSafeClient()
    return _client


def _split_sentences(email_text: str) -> list[str]:
    parts = [p.strip() for p in _SENTENCE_SPLIT_RE.split(email_text)]
    return [p for p in parts if p]


def _defect_questions(sentences: list[str]) -> dict:
    questions = {}
    for i in range(len(sentences)):
        questions[f"defect_{i}"] = Noul(
            instructions=(
                f"Does `sentences[{i}]` state that a specific product the "
                "customer purchased is defective, broken, damaged, faulty, "
                "or otherwise not working as expected?"
            ),
            criteria=NoulCriteria(
                true="Describes a specific purchased product having a defect, damage, or malfunction",
                false="Does not describe a defective product (e.g. shipping, billing, an unrelated topic, or a working product)",
            ),
        )
        if i > 0:
            questions[f"distinct_{i}"] = Noul(
                instructions=(
                    f"`sentences[{i}]` may or may not describe a defective product. "
                    f"If it does, is that defective product different from every "
                    f"defective product already described in `sentences[0..{i - 1}]`? "
                    f"Answer true if `sentences[{i}]` does not describe a defective product at all."
                ),
                criteria=NoulCriteria(
                    true="Not a defective-product sentence, or names a defective product not already covered earlier",
                    false="Names a defective product already described in an earlier sentence",
                ),
            )
    return questions


def _count_defective_products(sentences: list[str], answers: dict) -> int:
    count = 0
    for i in range(len(sentences)):
        if answers[f"defect_{i}"].noul <= DEFECT_NOUL_THRESHOLD:
            continue
        if i == 0 or answers[f"distinct_{i}"].noul > DISTINCT_NOUL_THRESHOLD:
            count += 1
    return count


def _date_questions(today: date) -> dict:
    years = {str(today.year - 1): None, str(today.year): None, str(today.year + 1): None}
    return {
        "date_mode": Choice(
            instructions=(
                "How is the delivery date the company promised the customer expressed "
                "in `email_text`, if at all?"
            ),
            criteria={
                "absolute": "A specific calendar date is given, e.g. 'September 20', '9/20/2026', 'Sept 20th'",
                "relative": "The date is given as a day-count or weekday relative to today, e.g. 'in 3 days', 'within a week', 'by next Friday'",
                "none": "No promised delivery date is stated anywhere in `email_text`",
            },
        ),
        "date_month": Choice(
            instructions=(
                "If `email_text` states an absolute promised delivery date, which month "
                "is it? Answer not_stated if no absolute date is given or the month is unclear."
            ),
            criteria={str(m): calendar.month_name[m] for m in range(1, 13)}
            | {"not_stated": "No absolute month given"},
        ),
        "date_day": Choice(
            instructions=(
                "If `email_text` states an absolute promised delivery date, which day of "
                "the month is it? Answer not_stated if no absolute date is given or the day is unclear."
            ),
            criteria={str(d): None for d in range(1, 32)} | {"not_stated": "No absolute day given"},
        ),
        "date_year": Choice(
            instructions=(
                "If `email_text` states an absolute promised delivery date and gives a "
                "year, which of these is it? Answer not_stated if no year is given."
            ),
            criteria=years | {"not_stated": "No year given"},
        ),
        "date_weekday": Choice(
            instructions=(
                "If `email_text` promises delivery relative to a weekday (e.g. 'by "
                "Friday', 'next Tuesday') rather than a specific day-count, which weekday "
                "is it? Answer not_stated otherwise."
            ),
            criteria={day: None for day in WEEKDAYS} | {"not_stated": "No weekday-based promise given"},
        ),
        "date_relative_days": Choice(
            instructions=(
                "If `email_text` promises delivery a certain number of days from today "
                "(e.g. 'within 3 days', 'in a week'), how many days is that? Treat 'a "
                "week' as 7, 'two weeks' as 14, 'a month' as 30. Answer not_stated if no "
                "such day-count is given (including if a weekday or absolute date was "
                "used instead), or other if a specific count outside this list was given."
            ),
            criteria={
                "0": "same day / today",
                "1": "the next day / tomorrow",
                "2": None,
                "3": None,
                "4": None,
                "5": None,
                "6": None,
                "7": "about a week",
                "10": None,
                "14": "about two weeks",
                "21": "about three weeks",
                "30": "about a month",
                "not_stated": "No day-count given",
                "other": "A specific day-count not listed above",
            },
        ),
    }


def _assemble_promised_date(answers: dict, today: date) -> Optional[date]:
    mode = answers["date_mode"].choice

    if mode == "absolute":
        month_s = answers["date_month"].choice
        day_s = answers["date_day"].choice
        year_s = answers["date_year"].choice
        if month_s == "not_stated" or day_s == "not_stated":
            return None
        year = today.year if year_s == "not_stated" else int(year_s)
        try:
            return date(year, int(month_s), int(day_s))
        except ValueError:
            return None

    if mode == "relative":
        weekday_s = answers["date_weekday"].choice
        if weekday_s != "not_stated":
            days_ahead = (WEEKDAYS.index(weekday_s) - today.weekday()) % 7
            return today + timedelta(days=days_ahead)
        days_s = answers["date_relative_days"].choice
        if days_s not in ("not_stated", "other"):
            return today + timedelta(days=int(days_s))
        return None

    return None


def check_email(email_text: str, today: date) -> dict:
    """Analyze a customer email for defective-product mentions and a delivery promise.

    Returns a dict with:
      - defective_product_count: number of distinct products the customer says are defective
      - promised_delivery_date: the promised delivery date as an ISO string, or None if
        the email doesn't state one clearly enough to resolve
      - delivery_date_passed: True/False if a promised date was resolved, else None
    """
    sentences = _split_sentences(email_text)

    state = {"email_text": email_text, "sentences": sentences}
    questions = _date_questions(today)
    questions.update(_defect_questions(sentences))

    client = _get_client()
    response = client.system_one(state=state, questions=questions, model=MODEL)

    defective_product_count = _count_defective_products(sentences, response.answers)
    promised_date = _assemble_promised_date(response.answers, today)

    return {
        "defective_product_count": defective_product_count,
        "promised_delivery_date": promised_date.isoformat() if promised_date else None,
        "delivery_date_passed": (promised_date < today) if promised_date else None,
    }
