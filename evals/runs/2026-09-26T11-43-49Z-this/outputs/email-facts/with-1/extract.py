import datetime
import re

from typesafe_sdk import Choice, Noul, NoulCriteria, TypeSafeClient

MODEL = "jev-1.13.0"

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_RE.split(text) if s.strip()]


def check_email(email_text: str, today: datetime.date) -> dict:
    """Returns {"defective_product_count": int, "promised_delivery_date": str | None, "delivery_date_passed": bool}."""
    sentences = _split_sentences(email_text)

    questions: dict[str, object] = {}
    for i in range(len(sentences)):
        questions[f"defective_{i}"] = Noul(
            instructions=(
                f"Does `sentences[{i}]` say that a specific product the customer "
                f"bought or received is defective, broken, damaged, faulty, or not working?"
            ),
            criteria=NoulCriteria(
                true="Names or clearly identifies one product as defective/broken/faulty/damaged/not working",
                false="No specific product is described as defective, or the sentence is about something else (e.g. shipping delay, price, praise)",
            ),
        )
        if i > 0:
            questions[f"new_product_{i}"] = Noul(
                instructions=(
                    f"If `sentences[{i}]` names a defective product, is that product "
                    f"different from every defective product already named in "
                    f"`sentences[0..{i - 1}]`? Answer true if `sentences[{i}]` does "
                    f"not name a defective product at all."
                ),
                criteria=NoulCriteria(
                    true="Names a defective product not mentioned earlier, or names no defective product",
                    false="Names a defective product that was already named in an earlier sentence",
                ),
            )

    questions["date_stated"] = Noul(
        instructions=(
            "Does `email` state a specific promised, expected, or guaranteed delivery "
            "date for an order (a calendar date, or something that resolves to one, "
            "such as 'by Friday the 12th')?"
        ),
        criteria=NoulCriteria(
            true="A specific calendar date for delivery is stated or clearly implied",
            false="No delivery date is given, or only a vague timeframe with no date (e.g. 'a few days', 'soon')",
        ),
    )
    questions["promised_month"] = Choice(
        instructions="What month is the promised delivery date in? If `email` states no specific delivery date, answer not_stated.",
        criteria={**{m: None for m in MONTHS}, "not_stated": "No specific delivery date is given"},
    )
    questions["promised_day"] = Choice(
        instructions="What day of the month (1-31) is the promised delivery date? If `email` states no specific delivery date, answer not_stated.",
        criteria={**{str(d): None for d in range(1, 32)}, "not_stated": "No specific delivery date is given"},
    )
    questions["promised_year"] = Choice(
        instructions=(
            f"What calendar year is the promised delivery date in? Today's date is "
            f"{today.isoformat()}; use it to resolve a year-less date (e.g. 'March 3rd') "
            f"to the nearest such date that is not in the past. If `email` states no "
            f"specific delivery date, answer not_stated."
        ),
        criteria={
            **{str(y): None for y in range(today.year - 1, today.year + 2)},
            "not_stated": "No specific delivery date is given",
        },
    )

    state = {"email": email_text, "sentences": sentences}
    with TypeSafeClient() as client:
        response = client.system_one(state=state, questions=questions, model=MODEL)

    defective_product_count = 0
    for i in range(len(sentences)):
        is_defective = response.nouls[f"defective_{i}"].noul > 0.5
        is_new = response.nouls[f"new_product_{i}"].noul > 0.5 if i > 0 else True
        if is_defective and is_new:
            defective_product_count += 1

    promised_delivery_date = None
    delivery_date_passed = False
    if response.nouls["date_stated"].noul > 0.5:
        month_choice = response.choices["promised_month"].choice
        day_choice = response.choices["promised_day"].choice
        year_choice = response.choices["promised_year"].choice
        if "not_stated" not in (month_choice, day_choice, year_choice):
            try:
                promised_delivery_date = datetime.date(
                    int(year_choice), MONTHS.index(month_choice) + 1, int(day_choice)
                )
                delivery_date_passed = promised_delivery_date < today
            except ValueError:
                promised_delivery_date = None

    return {
        "defective_product_count": defective_product_count,
        "promised_delivery_date": (
            promised_delivery_date.isoformat() if promised_delivery_date else None
        ),
        "delivery_date_passed": delivery_date_passed,
    }
