"""Read a customer email with typesafe.ai's Jev model.

Reports how many distinct defective products the customer describes, and
whether the delivery date they say was promised has already passed.
"""

from __future__ import annotations

import datetime
import re

from typesafe_sdk import Choice, Noul, NoulCriteria, TypeSafeClient

MODEL = "jev-1.13.0"

# Thresholds and weights live here so they're easy to find and tune together.
DEFECT_NOUL_THRESHOLD = 0.5
NEW_PRODUCT_NOUL_THRESHOLD = 0.5
DATE_STATED_NOUL_THRESHOLD = 0.5
DATE_CONFIDENCE_REVIEW_THRESHOLD = 0.60

MONTHS = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
YEAR_MIN, YEAR_MAX = 2015, 2035


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _defect_questions(sentences: list[str]) -> dict:
    questions = {}
    for i, _ in enumerate(sentences):
        questions[f"defect_{i}"] = Noul(
            instructions=(
                f"Does `sentences[{i}]` state that a specific product the customer bought "
                "is defective, broken, damaged, or otherwise not working as expected?"
            ),
            criteria=NoulCriteria(
                true="Names or clearly refers to a product and says it is defective, broken, damaged, or malfunctioning.",
                false="No product defect is described here (e.g. a shipping complaint, a price question, a greeting).",
            ),
        )
        if i > 0:
            questions[f"new_{i}"] = Noul(
                instructions=(
                    f"If `sentences[{i}]` describes a defective product, is that product different from "
                    f"every defective product already described in `sentences[0:{i}]`? Answer yes only "
                    "when it names a distinct product, not a restatement or continued description of a "
                    "product mentioned earlier."
                ),
                criteria=NoulCriteria(
                    true="A newly named defective product not covered by an earlier sentence.",
                    false="The same product already described earlier, or no defective product here at all.",
                ),
            )
    return questions


def _date_questions() -> dict:
    return {
        "delivery_date_stated": Noul(
            instructions=(
                "Does the email state a specific date, or a day relative to today, on which the "
                "customer was promised delivery?"
            ),
        ),
        "delivery_date_mode": Choice(
            instructions=(
                "How is the delivery date the customer says was promised to them expressed? "
                "'absolute' = a calendar date naming a month (e.g. 'March 3rd', '3/3'); "
                "'relative' = phrased relative to today or a named weekday (e.g. 'tomorrow', 'by Friday', "
                "'next Monday'); 'none' = no promised delivery date is stated."
            ),
            criteria={
                "absolute": None,
                "relative": None,
                "none": "No promised delivery date is stated in the email.",
            },
        ),
        "delivery_month": Choice(
            instructions="If the promised delivery date is an absolute calendar date, which month is it?",
            criteria={m: None for m in MONTHS} | {"none": "Not an absolute date, or the month isn't stated."},
        ),
        "delivery_day": Choice(
            instructions=(
                "If the promised delivery date is an absolute calendar date, which day of the month "
                "(1-31) is it?"
            ),
            criteria={str(d): None for d in range(1, 32)} | {"none": "Not an absolute date, or the day isn't stated."},
        ),
        "delivery_year": Choice(
            instructions=(
                "If the promised delivery date is an absolute calendar date and states a year, which "
                "year is it?"
            ),
            criteria={str(y): None for y in range(YEAR_MIN, YEAR_MAX + 1)} | {
                "not_stated": "No year is stated for the promised date.",
                "out_of_range": f"A year is stated but falls outside {YEAR_MIN}-{YEAR_MAX}.",
            },
        ),
        "delivery_day_anchor": Choice(
            instructions="If the promised delivery date is relative to today, which of these best describes it?",
            criteria={
                "today": None,
                "tomorrow": None,
                "day_after_tomorrow": None,
                "weekday": "A named day of the week (e.g. 'Friday', 'next Monday').",
                "none": "Not a relative date, or no clear anchor is stated.",
            },
        ),
        "delivery_weekday": Choice(
            instructions="If the promised delivery date names a day of the week, which one?",
            criteria={w: None for w in WEEKDAYS} | {"none": "No weekday is named."},
        ),
        "delivery_week_offset": Choice(
            instructions=(
                "If the promised delivery date names a day of the week, is it qualified as 'next' week, "
                "or unqualified/'this' week? Use 'current' for a bare weekday with no qualifier "
                "(e.g. just 'Friday')."
            ),
            criteria={"current": None, "next": None, "none": "No weekday is named."},
        ),
    }


def _resolve_weekday(weekday_name: str, offset: str, today: datetime.date) -> datetime.date:
    target = WEEKDAYS.index(weekday_name)
    days_ahead = (target - today.weekday()) % 7
    resolved = today + datetime.timedelta(days=days_ahead)
    if offset == "next":
        resolved += datetime.timedelta(days=7)
    return resolved


def _assemble_delivery_date(answers, today: datetime.date) -> tuple[datetime.date | None, float]:
    mode = answers.choices["delivery_date_mode"]
    stated = answers.nouls["delivery_date_stated"].noul

    if mode.choice == "none" or stated < DATE_STATED_NOUL_THRESHOLD:
        return None, mode.confidence

    if mode.choice == "absolute":
        month_a = answers.choices["delivery_month"]
        day_a = answers.choices["delivery_day"]
        year_a = answers.choices["delivery_year"]
        if month_a.choice == "none" or day_a.choice == "none":
            return None, min(mode.confidence, month_a.confidence, day_a.confidence)

        month = MONTHS.index(month_a.choice) + 1
        day = int(day_a.choice)
        year_stated = year_a.choice not in ("not_stated", "out_of_range")
        year = int(year_a.choice) if year_stated else today.year

        try:
            resolved = datetime.date(year, month, day)
        except ValueError:
            return None, 0.0

        if not year_stated and resolved < today - datetime.timedelta(days=31):
            resolved = datetime.date(year + 1, month, day)

        confidence = min(mode.confidence, month_a.confidence, day_a.confidence, year_a.confidence)
        return resolved, confidence

    # mode.choice == "relative"
    anchor = answers.choices["delivery_day_anchor"]
    if anchor.choice == "today":
        return today, min(mode.confidence, anchor.confidence)
    if anchor.choice == "tomorrow":
        return today + datetime.timedelta(days=1), min(mode.confidence, anchor.confidence)
    if anchor.choice == "day_after_tomorrow":
        return today + datetime.timedelta(days=2), min(mode.confidence, anchor.confidence)
    if anchor.choice == "weekday":
        weekday_a = answers.choices["delivery_weekday"]
        offset_a = answers.choices["delivery_week_offset"]
        if weekday_a.choice == "none":
            return None, min(mode.confidence, anchor.confidence)
        resolved = _resolve_weekday(weekday_a.choice, offset_a.choice, today)
        confidence = min(mode.confidence, anchor.confidence, weekday_a.confidence, offset_a.confidence)
        return resolved, confidence

    return None, mode.confidence


def check_email(email_text: str, today: datetime.date) -> dict:
    sentences = _split_sentences(email_text)

    questions = _defect_questions(sentences)
    questions.update(_date_questions())

    with TypeSafeClient() as client:
        response = client.system_one(
            state={"email": email_text, "sentences": sentences},
            questions=questions,
            model=MODEL,
        )

    defective_product_count = 0
    for i in range(len(sentences)):
        if response.nouls[f"defect_{i}"].noul < DEFECT_NOUL_THRESHOLD:
            continue
        if i == 0 or response.nouls[f"new_{i}"].noul >= NEW_PRODUCT_NOUL_THRESHOLD:
            defective_product_count += 1

    delivery_date, date_confidence = _assemble_delivery_date(response, today)

    return {
        "defective_product_count": defective_product_count,
        "promised_delivery_date": delivery_date.isoformat() if delivery_date else None,
        "delivery_date_passed": delivery_date < today if delivery_date else None,
        "delivery_date_needs_review": (
            delivery_date is not None and date_confidence < DATE_CONFIDENCE_REVIEW_THRESHOLD
        ),
        "model": response.model,
    }
