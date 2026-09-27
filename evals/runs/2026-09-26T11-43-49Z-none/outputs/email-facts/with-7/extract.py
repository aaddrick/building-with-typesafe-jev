import datetime

from typesafe_sdk import Noul, NoulCriteria, Score, TypeSafeClient


def check_email(email_text: str, today: datetime.date) -> dict:
    client = TypeSafeClient()

    questions = {
        "defective_product_count": Score(
            instructions="How many different products does the customer say are defective?",
            criteria=[
                "No products are described as defective",
                "Exactly one product is described as defective",
                "Exactly two different products are described as defective",
                "Three or more different products are described as defective",
            ],
        ),
        "delivery_date_passed": Noul(
            instructions=(
                f"Today's date is {today.isoformat()}. The customer refers to a date "
                "they were promised for delivery. Has that promised delivery date "
                "already passed as of today?"
            ),
            criteria=NoulCriteria(
                true="The promised delivery date is before today's date",
                false="The promised delivery date is today, in the future, or no delivery date is mentioned",
            ),
        ),
    }

    result = client.system_one(email_text, questions)

    # Score levels are 1-indexed, so the raw score is offset by 1 from the product count.
    raw_score = result.scores["defective_product_count"].score
    defective_product_count = max(0, round(raw_score) - 1)

    delivery_date_passed = result.nouls["delivery_date_passed"].noul > 0.5

    return {
        "defective_product_count": defective_product_count,
        "delivery_date_passed": delivery_date_passed,
    }
