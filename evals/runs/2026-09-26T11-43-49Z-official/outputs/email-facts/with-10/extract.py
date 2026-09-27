"""Analyze customer emails with TypeSafe's Jev model (System One)."""
from __future__ import annotations

import datetime

from typesafe_sdk import Noul, NoulCriteria, Score, TypeSafeClient

# Noul answers are a 0-1 probability of "yes"; 0.5 is the neutral midpoint.
NOUL_THRESHOLD = 0.5

# Score buckets for the defective-product count. The top bucket is a floor,
# not an exact count: a rounded score of 4 means "4 or more".
DEFECT_COUNT_LEVELS = [
    "No products are described as defective",
    "One product is described as defective",
    "Two products are described as defective",
    "Three products are described as defective",
    "Four or more products are described as defective",
]


def check_email(email_text: str, today: datetime.date) -> dict:
    """Read a customer email and report on defective products and delivery timing.

    Returns a dict with:
      - "defective_product_count": estimated number of distinct products the
        customer describes as defective/broken/damaged (int, capped at 4+).
      - "delivery_date_passed": True/False if the email mentions a promised or
        expected delivery date, indicating whether that date is already
        before `today`; None if no delivery date is mentioned at all.
    """
    state = {"email": email_text, "today": today.isoformat()}

    with TypeSafeClient() as client:
        response = client.system_one(
            state=state,
            questions={
                "defective_product_count": Score(
                    instructions=(
                        "How many distinct products does the customer describe "
                        "as defective, broken, damaged, or otherwise not working "
                        "in `state.email`? Count each distinct product once, "
                        "even if it is mentioned more than once."
                    ),
                    criteria=DEFECT_COUNT_LEVELS,
                ),
                "delivery_date_mentioned": Noul(
                    instructions=(
                        "Does `state.email` mention a delivery date that the "
                        "customer was promised or is expecting for any item, "
                        "whether given as a specific date, a relative "
                        "expression (e.g. 'next Tuesday'), or a timeframe?"
                    ),
                ),
                "delivery_date_passed": Noul(
                    instructions=(
                        "Compare the delivery date the customer was promised "
                        "or is expecting, as mentioned in `state.email`, to "
                        "`state.today`. Has that promised date already passed, "
                        "i.e. is it earlier than `state.today`?"
                    ),
                    criteria=NoulCriteria(
                        true="The promised delivery date is before state.today",
                        false=(
                            "The promised delivery date is on or after "
                            "state.today, or is too ambiguous to place"
                        ),
                    ),
                ),
            },
        )

    defective_product_count = round(response.scores["defective_product_count"].score)

    delivery_date_mentioned = (
        response.nouls["delivery_date_mentioned"].noul >= NOUL_THRESHOLD
    )
    delivery_date_passed = (
        response.nouls["delivery_date_passed"].noul >= NOUL_THRESHOLD
        if delivery_date_mentioned
        else None
    )

    return {
        "defective_product_count": defective_product_count,
        "delivery_date_passed": delivery_date_passed,
    }
