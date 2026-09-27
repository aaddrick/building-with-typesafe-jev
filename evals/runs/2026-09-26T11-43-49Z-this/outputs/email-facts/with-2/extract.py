"""Extract defect-count and delivery-date-passed facts from a customer email using Jev."""

import re
from datetime import date, timedelta

from typesafe_sdk import Choice, Noul, NoulCriteria, TypeSafeClient

MODEL = "jev-1.13.0"

DEFECT_CLAIM_THRESHOLD = 0.5
NEW_PRODUCT_THRESHOLD = 0.5
DATE_STATED_THRESHOLD = 0.5

_MONTH_OPTIONS = {str(m): None for m in range(1, 13)} | {
    "not_applicable": "The month of the promised delivery date is not stated, or no absolute date was given."
}
_DAY_OPTIONS = {str(d): None for d in range(1, 32)} | {
    "not_applicable": "The day of the promised delivery date is not stated, or no absolute date was given."
}
_YEAR_OFFSET_OPTIONS = {
    "last_year": "The promised delivery date falls in the calendar year before today's.",
    "this_year": "The promised delivery date falls in today's calendar year.",
    "next_year": "The promised delivery date falls in the calendar year after today's.",
    "not_applicable": "No absolute delivery date was given, or the year cannot be inferred.",
}
_DIRECTION_OPTIONS = {
    "past": "The delivery was promised to happen a certain amount of time before today (e.g. '3 days ago').",
    "future": "The delivery is promised a certain amount of time after today (e.g. 'in 5 days').",
    "not_applicable": "No relative delivery offset was given.",
}
_UNIT_OPTIONS = {
    "day": None,
    "week": None,
    "month": None,
    "not_applicable": "No relative delivery offset was given.",
}
_AMOUNT_OPTIONS = {str(n): None for n in range(1, 15)} | {
    "more_than_14": "The stated offset is more than 14 units.",
    "not_applicable": "No relative delivery offset was given.",
}

_client = TypeSafeClient()


def _split_sentences(email_text: str) -> list[str]:
    pieces = re.split(r"(?<=[.!?])\s+|\n+", email_text.strip())
    return [p.strip() for p in pieces if p.strip()]


def _count_defective_products(sentences: list[str]) -> int:
    count = 0
    confirmed_defect_sentences: list[str] = []
    for sentence in sentences:
        r = _client.system_one(
            state={
                "sentence": sentence,
                "already_confirmed_defective_products": confirmed_defect_sentences,
            },
            questions={
                "is_defective_claim": Noul(
                    instructions="Does `sentence` say that a specific product the customer bought is defective, broken, faulty, damaged, or otherwise not working?",
                    criteria=NoulCriteria(
                        true="Names or clearly refers to a product and says something is wrong with it",
                        false="No product defect is claimed here",
                    ),
                ),
                "is_new_product": Noul(
                    instructions=(
                        "Assume `sentence` claims a product is defective. Is that product different from "
                        "every product already listed in `already_confirmed_defective_products`?"
                    ),
                    criteria=NoulCriteria(
                        true="The product in `sentence` is not among those already listed",
                        false="The product in `sentence` is the same one already listed",
                    ),
                ),
            },
            model=MODEL,
        )
        if r.nouls["is_defective_claim"].noul < DEFECT_CLAIM_THRESHOLD:
            continue
        if confirmed_defect_sentences and r.nouls["is_new_product"].noul < NEW_PRODUCT_THRESHOLD:
            continue
        count += 1
        confirmed_defect_sentences.append(sentence)
    return count


def _assemble_delivery_date(choices: dict, today: date) -> date | None:
    mode = choices["date_mode"].choice
    if mode == "absolute":
        month, day, year_offset = (
            choices["month"].choice,
            choices["day"].choice,
            choices["year_offset"].choice,
        )
        if "not_applicable" in (month, day):
            return None
        year = today.year + {"last_year": -1, "this_year": 0, "next_year": 1}.get(year_offset, 0)
        try:
            return date(year, int(month), int(day))
        except ValueError:
            return None
    if mode == "relative":
        direction, unit, amount = (
            choices["direction"].choice,
            choices["unit"].choice,
            choices["amount"].choice,
        )
        if "not_applicable" in (direction, unit, amount):
            return None
        n = 15 if amount == "more_than_14" else int(amount)
        delta = {
            "day": timedelta(days=n),
            "week": timedelta(weeks=n),
            "month": timedelta(days=n * 30),
        }[unit]
        return today - delta if direction == "past" else today + delta
    return None


def _find_delivery_date(email_text: str, today: date) -> date | None:
    r = _client.system_one(
        state={"email": email_text, "today": today.isoformat()},
        questions={
            "date_stated": Noul(
                instructions=(
                    "Does the email state or clearly imply a specific date, or a day offset from today "
                    "(e.g. '3 days ago', 'in a week'), by which a product was promised to be delivered "
                    "to the customer?"
                ),
                criteria=NoulCriteria(
                    true="A promised delivery date or day offset is given somewhere in `email`",
                    false="No promised delivery date or day offset is given",
                ),
            ),
            "date_mode": Choice(
                instructions="How is the promised delivery date expressed in `email`?",
                criteria={
                    "absolute": "A specific calendar date or day is given, e.g. 'March 15', 'the 20th', '9/20'.",
                    "relative": "The timing is given only as an offset from today, e.g. '3 days ago', 'in 5 days'.",
                    "not_stated": "No promised delivery date is given anywhere in `email`.",
                },
            ),
            "month": Choice(
                instructions="If `date_mode` is absolute, which month was the promised delivery date in?",
                criteria=_MONTH_OPTIONS,
            ),
            "day": Choice(
                instructions="If `date_mode` is absolute, which day of the month was the promised delivery date?",
                criteria=_DAY_OPTIONS,
            ),
            "year_offset": Choice(
                instructions="If `date_mode` is absolute, which calendar year (relative to `today`) was the promised delivery date in?",
                criteria=_YEAR_OFFSET_OPTIONS,
            ),
            "direction": Choice(
                instructions="If `date_mode` is relative, is the promised delivery offset before or after `today`?",
                criteria=_DIRECTION_OPTIONS,
            ),
            "unit": Choice(
                instructions="If `date_mode` is relative, what time unit is the offset expressed in?",
                criteria=_UNIT_OPTIONS,
            ),
            "amount": Choice(
                instructions="If `date_mode` is relative, how many of that unit was the offset?",
                criteria=_AMOUNT_OPTIONS,
            ),
        },
        model=MODEL,
    )
    if r.nouls["date_stated"].noul < DATE_STATED_THRESHOLD:
        return None
    return _assemble_delivery_date(r.choices, today)


def check_email(email_text: str, today: date) -> dict:
    sentences = _split_sentences(email_text)
    defective_product_count = _count_defective_products(sentences)
    delivery_date = _find_delivery_date(email_text, today)

    return {
        "defective_product_count": defective_product_count,
        "delivery_date_promised": delivery_date is not None,
        "delivery_date": delivery_date.isoformat() if delivery_date else None,
        "delivery_date_passed": (delivery_date < today) if delivery_date else None,
    }
