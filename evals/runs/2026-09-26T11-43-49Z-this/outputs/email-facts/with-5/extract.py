"""Read a customer email with Jev and report:

- how many different products the customer says are defective
- whether the delivery date the company promised has already passed

Code owns counting and date math (see typesafe.ai docs, "keep math, counting,
and dates in code"); Jev only makes the per-sentence judgment calls.
"""

from __future__ import annotations

import datetime
import re

from typesafe_sdk import Choice, Noul, NoulCriteria, TypeSafeClient

MODEL = "jev-1.13.0"

MONTHS = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

# Tune these on labeled data from real support inboxes.
DEFECT_MENTION_THRESHOLD = 0.5
NEW_PRODUCT_THRESHOLD = 0.5
DATE_CONFIDENCE_REVIEW_THRESHOLD = 0.60

_client: TypeSafeClient | None = None


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        _client = TypeSafeClient(model=MODEL)
    return _client


def _split_sentences(text: str) -> list[str]:
    """Break the email body into candidate sentences for per-item counting."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _count_distinct_defective_products(client: TypeSafeClient, sentences: list[str]) -> int:
    """Count distinct defective products by asking two Nouls per sentence:
    does it name a defective product, and is that product new relative to
    every earlier sentence. Sum in code (see typesafe.ai docs on counting
    distinct items).
    """
    if not sentences:
        return 0

    questions: dict[str, Noul] = {}
    for i, _sentence in enumerate(sentences):
        questions[f"mentions_defect_{i}"] = Noul(
            instructions=(
                f"Does `sentences[{i}]` state that a specific product the customer "
                "received or purchased is defective, broken, damaged, malfunctioning, "
                "or arrived not working as expected?"
            ),
            criteria=NoulCriteria(
                true=(
                    "The sentence claims a specific product is defective, broken, "
                    "damaged, malfunctioning, or not working."
                ),
                false=(
                    "The sentence does not claim any product is defective (e.g. it "
                    "is about shipping, price, a greeting, or an unrelated complaint)."
                ),
            ),
        )
        if i > 0:
            questions[f"new_product_{i}"] = Noul(
                instructions=(
                    f"Assume `sentences[{i}]` states that a product is defective. Is "
                    f"the defective product it names a different product than every "
                    f"defective product already named in `sentences[0..{i - 1}]`?"
                ),
                criteria=NoulCriteria(
                    true=(
                        "The product named here is different from every defective "
                        "product named in an earlier sentence."
                    ),
                    false=(
                        "This is the same defective product already named in an "
                        "earlier sentence (a restatement, pronoun reference, or "
                        "continued description of the same item)."
                    ),
                ),
            )

    response = client.system_one(state={"sentences": sentences}, questions=questions)

    count = 0
    for i in range(len(sentences)):
        if response.nouls[f"mentions_defect_{i}"].noul <= DEFECT_MENTION_THRESHOLD:
            continue
        if i == 0:
            count += 1
            continue
        if response.nouls[f"new_product_{i}"].noul > NEW_PRODUCT_THRESHOLD:
            count += 1
    return count


def _extract_promised_delivery_date_parts(client: TypeSafeClient, email_text: str) -> dict:
    """Extract the promised delivery date as parts via Choices; code assembles
    the date (see typesafe.ai docs' date_extraction cookbook).
    """
    questions = {
        "mode": Choice(
            instructions=(
                "How is the delivery date that the company promised the customer "
                "written in `email`? 'absolute' = a calendar date naming a month, "
                "day, and/or year; 'relative' = given relative to today (e.g. "
                "'in 3 days', 'next Monday'); 'none' = no promised delivery date is "
                "stated anywhere in `email`."
            ),
            criteria={"absolute": None, "relative": None, "none": None},
        ),
        "month": Choice(
            instructions=(
                "If the promised delivery date in `email` is an absolute calendar "
                "date, which month is it in?"
            ),
            criteria={m: None for m in MONTHS} | {"none": "No month is stated."},
        ),
        "day": Choice(
            instructions=(
                "If the promised delivery date in `email` is an absolute calendar "
                "date, which day of the month (1-31) is it?"
            ),
            criteria={str(d): None for d in range(1, 32)} | {"none": "No day is stated."},
        ),
        "year": Choice(
            instructions=(
                "If the promised delivery date in `email` is an absolute calendar "
                "date, which year is it?"
            ),
            criteria={str(y): None for y in range(1900, 2051)}
            | {
                "out_of_range": "A year is stated but falls outside 1900-2050.",
                "none": "No year is stated.",
            },
        ),
        "day_anchor": Choice(
            instructions=(
                "If the promised delivery date in `email` is relative to today, "
                "which day is it?"
            ),
            criteria={
                "today": None,
                "tomorrow": None,
                "day_after": "The day after tomorrow.",
                "weekday": "A named day of the week (e.g. 'by Thursday').",
                "none": None,
            },
        ),
        "weekday": Choice(
            instructions=(
                "If the promised delivery date in `email` names a day of the week, "
                "which one?"
            ),
            criteria={w: None for w in WEEKDAYS} | {"none": "No weekday is stated."},
        ),
        "week_offset": Choice(
            instructions=(
                "If the promised delivery date in `email` names a weekday, is it "
                "this coming occurrence ('current', e.g. 'this Thursday' or a bare "
                "'Thursday') or explicitly the one after ('next', e.g. 'next "
                "Thursday')?"
            ),
            criteria={"current": None, "next": None, "none": None},
        ),
    }

    response = client.system_one(state={"email": email_text}, questions=questions)
    return {qid: response.choices[qid] for qid in questions}


def _monday_of_week(day: datetime.date) -> datetime.date:
    return day - datetime.timedelta(days=day.weekday())


def _resolve_weekday_date(weekday_name: str, offset: str, today: datetime.date) -> datetime.date:
    target = WEEKDAYS.index(weekday_name)
    current_week_date = _monday_of_week(today) + datetime.timedelta(days=target)
    if offset == "next":
        return current_week_date + datetime.timedelta(days=7)
    if offset == "current":
        return current_week_date
    # Bare weekday, no "this/next" qualifier: resolve to the next occurrence.
    if current_week_date >= today:
        return current_week_date
    return current_week_date + datetime.timedelta(days=7)


def _assemble_promised_delivery_date(
    parts: dict, today: datetime.date
) -> tuple[datetime.date | None, float]:
    """Turn extracted date parts into a concrete date plus the minimum
    confidence over the parts actually used.
    """
    mode = parts["mode"]
    confidences = [mode.confidence]

    if mode.choice == "none":
        return None, mode.confidence

    if mode.choice == "absolute":
        month_c, day_c, year_c = parts["month"], parts["day"], parts["year"]
        confidences += [month_c.confidence, day_c.confidence, year_c.confidence]
        if month_c.choice == "none" or day_c.choice == "none":
            return None, min(confidences)

        month = MONTHS.index(month_c.choice) + 1
        day = int(day_c.choice)

        if year_c.choice == "out_of_range":
            return None, min(confidences)
        if year_c.choice == "none":
            try:
                candidate = datetime.date(today.year, month, day)
            except ValueError:
                return None, min(confidences)
            if (candidate - today).days < -31:
                candidate = datetime.date(today.year + 1, month, day)
            return candidate, min(confidences)

        year = int(year_c.choice)
        try:
            return datetime.date(year, month, day), min(confidences)
        except ValueError:
            return None, min(confidences)

    if mode.choice == "relative":
        anchor_c = parts["day_anchor"]
        confidences.append(anchor_c.confidence)
        if anchor_c.choice == "today":
            return today, min(confidences)
        if anchor_c.choice == "tomorrow":
            return today + datetime.timedelta(days=1), min(confidences)
        if anchor_c.choice == "day_after":
            return today + datetime.timedelta(days=2), min(confidences)
        if anchor_c.choice == "weekday":
            weekday_c, offset_c = parts["weekday"], parts["week_offset"]
            confidences += [weekday_c.confidence, offset_c.confidence]
            if weekday_c.choice == "none":
                return None, min(confidences)
            return (
                _resolve_weekday_date(weekday_c.choice, offset_c.choice, today),
                min(confidences),
            )
        return None, min(confidences)

    return None, min(confidences)


def check_email(email_text: str, today: datetime.date) -> dict:
    """Analyze a customer email and report:

    - defective_product_count: how many distinct products the customer says
      are defective.
    - delivery_date_passed: True/False if the promised delivery date is
      stated (compared to `today`), otherwise None if no delivery promise
      is stated in the email.

    Also returns the assembled date and confidence for auditing.
    """
    client = _get_client()

    sentences = _split_sentences(email_text)
    defective_product_count = _count_distinct_defective_products(client, sentences)

    date_parts = _extract_promised_delivery_date_parts(client, email_text)
    promised_date, date_confidence = _assemble_promised_delivery_date(date_parts, today)

    delivery_date_passed = None if promised_date is None else promised_date < today

    return {
        "defective_product_count": defective_product_count,
        "promised_delivery_date": promised_date.isoformat() if promised_date else None,
        "delivery_date_passed": delivery_date_passed,
        "date_confidence": date_confidence,
        "needs_review": promised_date is not None and date_confidence < DATE_CONFIDENCE_REVIEW_THRESHOLD,
        "model": MODEL,
    }
