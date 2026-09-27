import datetime

from typesafe_sdk import Noul, NoulCriteria, Score, TypeSafeClient


def check_email(email_text: str, today: datetime.date) -> dict:
    """Read a customer email and report the defective product count and
    whether the promised delivery date has already passed."""
    # today is embedded in the state so the model has a reference point to
    # compare against any delivery date mentioned in the email.
    state = {
        "email": email_text,
        "today": today.isoformat(),
    }

    with TypeSafeClient() as client:
        response = client.system_one(
            state=state,
            questions={
                "defective_product_count": Score(
                    instructions=(
                        "How many different products does the customer "
                        "describe as defective, broken, or faulty?"
                    ),
                    criteria=[
                        "No products are described as defective",
                        "Exactly one product is described as defective",
                        "Exactly two different products are described as defective",
                        "Three or more different products are described as defective",
                    ],
                ),
                "delivery_overdue": Noul(
                    instructions=(
                        "The customer mentions a promised or expected delivery "
                        "date, and that date is earlier than the 'today' value "
                        "given in the state."
                    ),
                    criteria=NoulCriteria(
                        true="A promised delivery date is mentioned and it is before 'today'",
                        false="No promised delivery date is mentioned, or it is on/after 'today'",
                    ),
                ),
            },
        )

    return {
        "defective_product_count": round(response.answers["defective_product_count"].score),
        "delivery_date_passed": response.answers["delivery_overdue"].noul >= 0.5,
    }
