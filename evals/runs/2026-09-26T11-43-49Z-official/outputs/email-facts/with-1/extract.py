"""Read a customer support email with TypeSafe's Jev model.

Reports how many distinct products the customer claims are defective, and
whether a delivery date promised to the customer has already passed.

Requires the TYPESAFE_API_KEY environment variable (see
https://console.typesafe.ai/).
"""

import re
from datetime import date, datetime
from typing import Optional

from typesafe_sdk import Choice, Score, TypeSafeClient

_MONTH = (
    r"(?:January|February|March|April|May|June|July|August|September|October"
    r"|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
)

# Recall-tuned: catches common explicit calendar-date spellings. It will miss
# relative phrasing ("next Tuesday", "in five business days"); those emails
# fall back to promised_delivery_date=None below.
_DATE_PATTERN = re.compile(
    r"""
    (?:
        MONTH\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}   # Month D, YYYY
      | MONTH\.?\s+\d{1,2}(?:st|nd|rd|th)?               # Month D
      | \d{1,2}\s+MONTH\.?,?\s+\d{4}                     # D Month YYYY
      | \d{4}-\d{2}-\d{2}                                # YYYY-MM-DD
      | \d{1,2}/\d{1,2}/\d{4}                            # MM/DD/YYYY
    )
    """.replace("MONTH", _MONTH),
    re.VERBOSE | re.IGNORECASE,
)

_DATE_FORMATS = [
    "%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%b %d %Y",
    "%d %B %Y", "%d %b %Y",
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%B %d", "%b %d",
]

_PRODUCT_COUNT_LEVELS = [
    "No product is described as defective or not working.",
    "Exactly one distinct product is described as defective.",
    "Exactly two distinct products are described as defective.",
    "Exactly three distinct products are described as defective.",
    "Four or more distinct products are described as defective.",
]


def _parse_date_span(span: str, today: date) -> Optional[date]:
    cleaned = re.sub(r"(\d)(st|nd|rd|th)", r"\1", span, flags=re.IGNORECASE)
    cleaned = cleaned.strip().rstrip(",")
    for fmt in _DATE_FORMATS:
        try:
            parsed = datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
        if "%Y" not in fmt:
            parsed = parsed.replace(year=today.year)
        return parsed.date()
    return None


def check_email(email_text: str, today: date) -> dict:
    date_candidates = sorted(
        {m.group(0) for m in _DATE_PATTERN.finditer(email_text)}
    )

    questions = {
        "defective_product_count": Score(
            instructions=(
                "How many different products does the customer say are "
                "defective or not working in this email?"
            ),
            criteria=_PRODUCT_COUNT_LEVELS,
        ),
    }
    if date_candidates:
        questions["promised_delivery_date"] = Choice(
            instructions=(
                "Which of these dates, if any, is the delivery date that "
                "was promised to the customer for their order? Do not pick "
                "a date that is only an order date, an email timestamp, or "
                "otherwise unrelated to when the order was promised to "
                "arrive."
            ),
            criteria={
                **{candidate: None for candidate in date_candidates},
                "none": "No listed date is a promised delivery date.",
            },
        )

    with TypeSafeClient() as client:
        result = client.system_one(email_text, questions)

    count_probabilities = result.scores["defective_product_count"].probabilities
    defective_product_count = max(count_probabilities, key=count_probabilities.get)

    promised_delivery_date: Optional[str] = None
    delivery_date_passed: Optional[bool] = None
    if date_candidates:
        chosen = result.choices["promised_delivery_date"].choice
        if chosen != "none":
            promised_delivery_date = chosen
            parsed = _parse_date_span(chosen, today)
            if parsed is not None:
                delivery_date_passed = parsed < today

    return {
        "defective_product_count": defective_product_count,
        "promised_delivery_date": promised_delivery_date,
        "delivery_date_passed": delivery_date_passed,
    }
