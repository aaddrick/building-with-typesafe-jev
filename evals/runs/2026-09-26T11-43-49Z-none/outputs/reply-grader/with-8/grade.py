from typesafe_sdk import Noul, Score, TypeSafeClient

MODEL = "jev-latest"

# Ordered worst -> best; index 0 maps to a final score of 1, index 9 to 10.
OVERALL_CRITERIA = [
    "Rude, contradicts what the customer said, and ignores the issue entirely",
    "Rude or inconsistent with the customer's message, and the issue is not addressed",
    "Polite but inconsistent with the customer's message, or the issue is not addressed",
    "Consistent and polite, but the issue is not resolved and no next step is given",
    "Consistent and polite, issue only partially addressed with vague next steps",
    "Consistent and polite, issue partially resolved",
    "Consistent and polite, resolves most of the issue",
    "Consistent, polite, and fully resolves the issue",
    "Consistent, polite, fully resolves the issue, and is proactive and clear",
    "Consistent, polite, fully resolves the issue, and exceeds expectations",
]

# Each entry is phrased as a violation; a high `noul` probability means the
# problem is present in the reply.
PROBLEM_CHECKS = {
    "inconsistent": "The reply is inconsistent with what the customer said.",
    "impolite": "The reply is not polite.",
    "unresolved": "The reply does not resolve the customer's issue.",
    "refund_promised": (
        "The reply promises, offers, or guarantees a refund, "
        "but only billing may promise refunds."
    ),
}

PROBLEM_THRESHOLD = 0.5


def grade(customer_message: str, agent_reply: str) -> dict:
    """Grade a support agent's reply on a 1-10 scale against the team rubric.

    Returns a dict with a "score" (1-10) and a "problems" list describing
    any rubric violations found.
    """
    with TypeSafeClient() as client:
        response = client.system_one(
            state={
                "customer_message": customer_message,
                "agent_reply": agent_reply,
            },
            model=MODEL,
            questions={
                "overall": Score(
                    instructions=(
                        "Rate the agent's reply to the customer. A good reply "
                        "stays consistent with what the customer actually said, "
                        "is polite, and resolves the customer's issue."
                    ),
                    criteria=OVERALL_CRITERIA,
                ),
                **{
                    name: Noul(instructions=f"{description} Is that true of this reply?")
                    for name, description in PROBLEM_CHECKS.items()
                },
            },
        )

    score = round(response.scores["overall"].score + 1, 1)
    problems = [
        description
        for name, description in PROBLEM_CHECKS.items()
        if response.nouls[name].noul >= PROBLEM_THRESHOLD
    ]

    return {"score": score, "problems": problems}
