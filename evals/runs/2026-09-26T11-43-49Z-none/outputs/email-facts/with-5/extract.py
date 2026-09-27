import datetime

from typesafe_sdk import Noul, Score, TypeSafeClient

client = TypeSafeClient()

# Score has no "extract N items" primitive, so distinct defective products are
# read off an ordered rubric instead; anything at the top level is reported as
# "4 or more" since the rubric can't distinguish further.
_DEFECTIVE_COUNT_LEVELS = [
    "No products are described as defective.",
    "Exactly one product is described as defective.",
    "Exactly two different products are described as defective.",
    "Exactly three different products are described as defective.",
    "Four or more different products are described as defective.",
]


def check_email(email_text: str, today: datetime.date) -> dict:
    response = client.system_one(
        state=email_text,
        questions={
            "defective_count": Score(
                instructions=(
                    "How many different products does the customer say are "
                    "defective in `email_text`?"
                ),
                criteria=_DEFECTIVE_COUNT_LEVELS,
            ),
            "delivery_late": Noul(
                instructions=(
                    f"As of {today.isoformat()}, the delivery date that was "
                    "promised to the customer in `email_text` has already passed."
                ),
            ),
        },
    )

    defective_count = round(response.answers["defective_count"].score)
    defective_count = max(0, min(defective_count, len(_DEFECTIVE_COUNT_LEVELS) - 1))

    return {
        "defective_product_count": defective_count,
        "delivery_date_passed": response.answers["delivery_late"].noul > 0.5,
    }
