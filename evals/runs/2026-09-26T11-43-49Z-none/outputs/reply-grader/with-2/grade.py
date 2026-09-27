from typesafe_sdk import Noul, Score, TypeSafeClient

MODEL = "jev-latest"

# Score criteria are ordered worst-to-best; the resulting level (0-9) is
# shifted by one to land on the requested 1-10 scale.
QUALITY_LEVELS = [
    "Reply contradicts what the customer said, is rude or dismissive, completely "
    "fails to address the customer's issue, and improperly promises a refund.",
    "Reply contradicts what the customer said, is rude or dismissive, and fails "
    "to resolve the issue.",
    "Reply is rude or dismissive and fails to resolve the issue, even though it "
    "does not contradict the customer.",
    "Reply is polite but is inconsistent with what the customer said and does "
    "not resolve the issue.",
    "Reply is polite and consistent with the customer's message, but does not "
    "resolve the issue and improperly promises a refund.",
    "Reply is polite and consistent with the customer's message, but only "
    "partially resolves the issue.",
    "Reply is polite, consistent with the customer's message, and resolves the "
    "issue, but improperly promises a refund.",
    "Reply is polite, consistent with the customer's message, and mostly "
    "resolves the issue, with minor gaps.",
    "Reply is polite, consistent with the customer's message, and fully "
    "resolves the issue.",
    "Reply is polite, fully consistent with the customer's message, completely "
    "and clearly resolves the issue, and appropriately avoids promising any "
    "refund.",
]

PROBLEM_QUESTIONS = {
    "inconsistent": (
        "The agent's reply contains claims or statements that contradict or "
        "misrepresent what the customer said in their message.",
        "Reply is inconsistent with what the customer said.",
    ),
    "impolite": (
        "The agent's reply is impolite, rude, dismissive, or otherwise "
        "unprofessional toward the customer.",
        "Reply is not polite.",
    ),
    "unresolved": (
        "The agent's reply fails to resolve or make meaningful progress on "
        "the customer's issue.",
        "Reply does not resolve the customer's issue.",
    ),
    "refund_promised": (
        "The agent's reply promises, guarantees, or otherwise commits to "
        "giving the customer a refund. Only the billing team is allowed to "
        "promise refunds, so any such promise in this reply is against policy.",
        "Reply improperly promises a refund.",
    ),
}


def grade(customer_message: str, agent_reply: str) -> dict:
    client = TypeSafeClient()

    state = {
        "customer_message": customer_message,
        "agent_reply": agent_reply,
    }

    questions = {
        "quality": Score(
            instructions=(
                "Grade the agent's reply to the customer's message against "
                "the rubric levels: consistency with what the customer said, "
                "politeness, whether it resolves the issue, and whether it "
                "improperly promises a refund."
            ),
            criteria=QUALITY_LEVELS,
        ),
    }
    for name, (instructions, _) in PROBLEM_QUESTIONS.items():
        questions[name] = Noul(instructions=instructions)

    response = client.system_one(state=state, model=MODEL, questions=questions)

    score = response.scores["quality"].score + 1
    score = max(1.0, min(10.0, round(score, 2)))

    problems = [
        message
        for name, (_, message) in PROBLEM_QUESTIONS.items()
        if response.nouls[name].noul
    ]

    return {"score": score, "problems": problems}
