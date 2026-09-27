import datetime

from typesafe_sdk import Noul, NoulCriteria, Score, TypeSafeClient


def check_email(email_text: str, today: datetime.date) -> dict:
    """Use Jev to report defective product count and delivery-date status from a customer email."""
    client = TypeSafeClient()

    response = client.system_one(
        state={"email": email_text, "today": today.isoformat()},
        questions={
            "defective_count": Score(
                instructions="How many different products does the customer say are defective?",
                criteria=[
                    "No defective products mentioned",
                    "Exactly one defective product",
                    "Exactly two defective products",
                    "Exactly three defective products",
                    "Exactly four defective products",
                    "Five or more defective products",
                ],
            ),
            "delivery_date_mentioned": Noul(
                instructions="The email states a specific delivery date that the company promised the customer",
            ),
            "delivery_date_passed": Noul(
                instructions=(
                    "The delivery date promised to the customer in the email has "
                    "already passed, given today's date in state"
                ),
                criteria=NoulCriteria(
                    true="The promised delivery date is earlier than today's date",
                    false="The promised delivery date is today or later, or no date was promised",
                ),
            ),
        },
    )

    defective_count = round(response.scores["defective_count"].score)
    date_mentioned = response.nouls["delivery_date_mentioned"].noul > 0.5
    date_passed = (
        response.nouls["delivery_date_passed"].noul > 0.5 if date_mentioned else None
    )

    return {
        "defective_product_count": defective_count,
        "delivery_date_passed": date_passed,
    }
