"""Read a customer email with typesafe.ai's Jev model.

Reports how many distinct products the customer says are defective, and
whether the delivery date they were promised has already passed.
"""

from __future__ import annotations

import re
from datetime import date

from typesafe_sdk import Choice, Noul, NoulCriteria, TypeSafeClient

MODEL = "jev-1.13.0"

# Thresholds, tuned against MODEL. Review together if answers look off.
DEFECTIVE_THRESHOLD = 0.5
DIFFERENT_PRODUCT_THRESHOLD = 0.5
DATE_STATED_THRESHOLD = 0.5
DATE_CONFIDENCE_FLOOR = 0.60  # below this, treat the assembled date as unreliable

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

_client: TypeSafeClient | None = None


def _get_client() -> TypeSafeClient:
    # Reused across calls: the SDK docs ask for one long-lived client, not one per request.
    global _client
    if _client is None:
        _client = TypeSafeClient()
    return _client


def _split_sentences(email_text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(email_text.strip()) if s.strip()]


def _build_defect_questions(sentences: list[str]) -> dict:
    questions: dict[str, object] = {}
    for i in range(len(sentences)):
        questions[f"defective_{i}"] = Noul(
            instructions=(
                f"Does `sentences[{i}]` state that a specific product is defective, "
                f"broken, faulty, damaged, or otherwise not working?"
            ),
            criteria=NoulCriteria(
                true="States a specific product has a defect or is not working",
                false="Does not claim any product is defective",
            ),
        )
        if i > 0:
            questions[f"different_{i}"] = Noul(
                instructions=(
                    f"Assuming `sentences[{i}]` states that a product is defective, is that "
                    f"product different from every product already stated to be defective in "
                    f"the earlier sentences (`sentences[0:{i}]`)?"
                ),
                criteria=NoulCriteria(
                    true="A different, not-yet-mentioned defective product",
                    false="The same defective product already mentioned earlier",
                ),
            )
    return questions


def _build_date_questions(today: date) -> dict:
    # Customer emails discuss recent orders, so a stated year (if any) should fall near today.
    year_options = {
        str(today.year - 1): None,
        str(today.year): None,
        str(today.year + 1): None,
        "not_stated": "No year is stated or implied for the promised delivery date",
    }
    month_options = {str(n): name for n, name in enumerate(MONTH_NAMES, start=1)}
    month_options["not_stated"] = "No month is stated for the promised delivery date"
    day_options = {str(d): None for d in range(1, 32)}
    day_options["not_stated"] = "No day of the month is stated for the promised delivery date"

    return {
        "delivery_date_stated": Noul(
            instructions=(
                "Does the email state or clearly imply a specific date (a day and month) by "
                "which the product was promised to be delivered?"
            ),
            criteria=NoulCriteria(
                true="A specific promised delivery date is given",
                false="No specific promised delivery date is given",
            ),
        ),
        "delivery_month": Choice(
            instructions=(
                "If the email states a promised delivery date, what month is it? Answer "
                "`not_stated` if no month is given."
            ),
            criteria=month_options,
        ),
        "delivery_day": Choice(
            instructions=(
                "If the email states a promised delivery date, what day of the month is it? "
                "Answer `not_stated` if no day is given."
            ),
            criteria=day_options,
        ),
        "delivery_year": Choice(
            instructions=(
                "If the email states or implies a year for the promised delivery date, which "
                "year is it? Answer `not_stated` if no year is given or implied."
            ),
            criteria=year_options,
        ),
    }


def _count_defective_products(response, sentence_count: int) -> int:
    count = 0
    for i in range(sentence_count):
        if response.nouls[f"defective_{i}"].noul <= DEFECTIVE_THRESHOLD:
            continue
        # The first defective mention is vacuously "different" from an empty set.
        if i == 0 or response.nouls[f"different_{i}"].noul > DIFFERENT_PRODUCT_THRESHOLD:
            count += 1
    return count


def _resolve_promised_delivery_date(response, today: date) -> date | None:
    if response.nouls["delivery_date_stated"].noul <= DATE_STATED_THRESHOLD:
        return None

    month_answer = response.choices["delivery_month"]
    day_answer = response.choices["delivery_day"]
    year_answer = response.choices["delivery_year"]

    if month_answer.choice == "not_stated" or day_answer.choice == "not_stated":
        return None

    year_confidence = 1.0 if year_answer.choice == "not_stated" else year_answer.confidence
    date_confidence = min(month_answer.confidence, day_answer.confidence, year_confidence)
    if date_confidence < DATE_CONFIDENCE_FLOOR:
        return None

    year = today.year if year_answer.choice == "not_stated" else int(year_answer.choice)
    try:
        return date(year, int(month_answer.choice), int(day_answer.choice))
    except ValueError:
        return None  # e.g. Feb 30 -- an impossible assembled date


def check_email(email_text: str, today: date) -> dict:
    sentences = _split_sentences(email_text)
    if not sentences:
        return {
            "defective_product_count": 0,
            "promised_delivery_date": None,
            "delivery_date_passed": None,
        }

    questions = _build_defect_questions(sentences)
    questions.update(_build_date_questions(today))

    response = _get_client().system_one(
        state={"email_text": email_text, "sentences": sentences},
        questions=questions,
        model=MODEL,
    )

    promised_delivery_date = _resolve_promised_delivery_date(response, today)

    return {
        "defective_product_count": _count_defective_products(response, len(sentences)),
        "promised_delivery_date": (
            promised_delivery_date.isoformat() if promised_delivery_date else None
        ),
        "delivery_date_passed": (
            promised_delivery_date < today if promised_delivery_date else None
        ),
    }
