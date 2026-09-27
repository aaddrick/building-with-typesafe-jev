import datetime

from typesafe_sdk import Choice, Noul, TypeSafeClient


def check_email(email_text: str, today: datetime.date) -> dict:
    with TypeSafeClient() as client:
        response = client.system_one(
            state={
                "today": today.isoformat(),
                "email": email_text,
            },
            questions={
                "defective_product_count": Choice(
                    instructions="How many distinct products does the customer say are defective?",
                    criteria={
                        "0": "The customer does not report any defective product.",
                        "1": "The customer reports exactly one defective product.",
                        "2": "The customer reports exactly two distinct defective products.",
                        "3": "The customer reports exactly three distinct defective products.",
                        "4+": "The customer reports four or more distinct defective products.",
                    },
                ),
                "delivery_late": Noul(
                    instructions=(
                        "The email promises a delivery date for an order, and that date "
                        "(compared against 'today' in the state) has already passed. "
                        "Answer false if no delivery date was promised."
                    ),
                ),
            },
        )

    count_choice = response.answers["defective_product_count"].choice
    defective_product_count = 4 if count_choice == "4+" else int(count_choice)

    return {
        "defective_product_count": defective_product_count,
        "delivery_date_passed": response.answers["delivery_late"].noul >= 0.5,
    }
