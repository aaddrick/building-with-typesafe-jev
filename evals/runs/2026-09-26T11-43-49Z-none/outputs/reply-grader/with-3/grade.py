from typesafe_sdk import Noul, Score, TypeSafeClient

REFUND_THRESHOLD = 0.5
CHECK_THRESHOLD = 0.5

OVERALL_CRITERIA = [
    "Rude or dismissive, contradicts the customer, and leaves the issue unresolved",
    "Unhelpful and largely unresolved, with notable politeness or consistency problems",
    "Unresolved and somewhat inconsistent or curt",
    "Attempts to help but leaves the issue unresolved",
    "Partially resolves the issue with a passable tone",
    "Resolves the issue but with minor tone or consistency issues",
    "Resolves the issue politely with only trivial nitpicks",
    "Resolves the issue well, polite and consistent throughout",
    "Fully resolves the issue, polite, accurate, and well-written",
    "Exemplary reply: fully resolves the issue, warm and polite, perfectly "
    "consistent with the customer, and policy-compliant",
]


def grade(customer_message: str, agent_reply: str) -> dict:
    with TypeSafeClient() as client:
        response = client.system_one(
            state={
                "customer_message": customer_message,
                "agent_reply": agent_reply,
            },
            questions={
                "consistent": Noul(
                    instructions=(
                        "Does the agent's reply accurately reflect and stay "
                        "consistent with what the customer said, without "
                        "misrepresenting or contradicting it?"
                    ),
                ),
                "polite": Noul(
                    instructions="Is the agent's reply polite and respectful?",
                ),
                "resolves_issue": Noul(
                    instructions=(
                        "Does the agent's reply actually resolve the "
                        "customer's issue, rather than just acknowledging it?"
                    ),
                ),
                "promises_refund": Noul(
                    instructions=(
                        "Does the agent's reply promise, offer, or commit to "
                        "a refund? Only the billing team is allowed to "
                        "promise refunds, so any refund promise from a "
                        "general support agent violates policy."
                    ),
                ),
                "overall": Score(
                    instructions=(
                        "Rate the quality of the support agent's reply to "
                        "the customer, judged against this rubric: staying "
                        "consistent with what the customer said, being "
                        "polite, actually resolving the issue, and not "
                        "promising a refund (only billing may promise "
                        "refunds)."
                    ),
                    criteria=OVERALL_CRITERIA,
                ),
            },
        )

    answers = response.answers

    problems = []
    if answers["consistent"].noul < CHECK_THRESHOLD:
        problems.append("Reply is inconsistent with what the customer said.")
    if answers["polite"].noul < CHECK_THRESHOLD:
        problems.append("Reply is not polite.")
    if answers["resolves_issue"].noul < CHECK_THRESHOLD:
        problems.append("Reply does not resolve the customer's issue.")
    if answers["promises_refund"].noul >= REFUND_THRESHOLD:
        problems.append("Reply promises a refund, which only billing may do.")

    # OVERALL_CRITERIA has 10 levels indexed 0-9; shift to a 1-10 scale.
    score = round(answers["overall"].score) + 1

    return {
        "score": score,
        "problems": problems,
    }
