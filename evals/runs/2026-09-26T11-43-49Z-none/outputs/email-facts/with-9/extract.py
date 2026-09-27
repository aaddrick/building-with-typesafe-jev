import datetime

from typesafe_sdk import Noul, NoulCriteria, Score, TypeSafeClient

_DEFECTIVE_COUNT_LEVELS = [
    "No products are described as defective",
    "One product is described as defective",
    "Two different products are described as defective",
    "Three different products are described as defective",
    "Four different products are described as defective",
    "Five or more different products are described as defective",
]


def check_email(email_text: str, today: datetime.date) -> dict:
    with TypeSafeClient() as client:
        response = client.system_one(
            state={"email": email_text, "today": today.isoformat()},
            questions={
                "defective_count": Score(
                    instructions="How many different products does the customer say are defective?",
                    criteria=_DEFECTIVE_COUNT_LEVELS,
                ),
                "delivery_late": Noul(
                    instructions=(
                        "The delivery date the customer was promised in the email "
                        "has already passed as of 'today' in the state."
                    ),
                    criteria=NoulCriteria(
                        true="The promised delivery date is before 'today', or the email says the delivery is overdue",
                        false="The promised delivery date is on or after 'today', or no delivery date was promised",
                    ),
                ),
            },
        )

    # Score levels are indexed 0..5, matching the defect counts they describe.
    max_count = len(_DEFECTIVE_COUNT_LEVELS) - 1
    defective_count = round(response.answers["defective_count"].score)
    defective_count = max(0, min(defective_count, max_count))

    return {
        "defective_product_count": defective_count,
        "delivery_date_passed": response.answers["delivery_late"].noul > 0.5,
    }
