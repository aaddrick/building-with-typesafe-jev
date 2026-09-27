"""Grade a support agent's reply against the team rubric using TypeSafe's Jev model."""

from typesafe_sdk import Noul, Score, TypeSafeClient

CONSISTENCY_CRITERIA = [
    "The reply contradicts or misstates something the customer said (wrong issue, wrong "
    "order/account details, wrong request).",
    "The reply is broadly consistent with what the customer said but glosses over or "
    "slightly misreads a detail.",
    "The reply accurately reflects and directly engages with what the customer actually said.",
]

POLITENESS_CRITERIA = [
    "Rude, dismissive, condescending, or otherwise unprofessional in tone.",
    "Neutral and businesslike; not rude, but lacking warmth or courtesy.",
    "Polite, respectful, and courteous throughout.",
]

RESOLUTION_CRITERIA = [
    "Does not address the customer's actual problem, or leaves it entirely unresolved.",
    "Partially addresses the problem or gives a next step, but does not resolve it outright.",
    "Fully resolves the customer's issue or gives a complete, actionable solution.",
]

REFUND_INSTRUCTIONS = (
    "Does the agent's reply promise, guarantee, or commit to giving the customer a refund "
    "(e.g. 'we will refund you', 'you'll get your money back', 'I've processed a refund')? "
    "Only the billing team is allowed to promise refunds, so any refund commitment made by "
    "this agent is a policy violation."
)

# Score levels are 0-indexed; a level below this is treated as a rubric failure.
FAILING_LEVEL = 1.5


def grade(customer_message: str, agent_reply: str) -> dict:
    """Grade a support agent's reply on a 1-10 scale against the support rubric.

    Returns a dict with:
      - "score": int from 1 (worst) to 10 (best)
      - "problems": list of human-readable rubric violations found, if any
    """
    with TypeSafeClient() as client:
        result = client.system_one(
            state={
                "customer_message": customer_message,
                "agent_reply": agent_reply,
            },
            questions={
                "consistency": Score(
                    instructions=(
                        "Judge whether the agent's reply is consistent with what the "
                        "customer said in `customer_message`."
                    ),
                    criteria=CONSISTENCY_CRITERIA,
                ),
                "politeness": Score(
                    instructions="Judge the tone of the agent's reply toward the customer.",
                    criteria=POLITENESS_CRITERIA,
                ),
                "resolution": Score(
                    instructions=(
                        "Judge how completely the agent's reply resolves the issue the "
                        "customer raised in `customer_message`."
                    ),
                    criteria=RESOLUTION_CRITERIA,
                ),
                "refund_promise": Noul(instructions=REFUND_INSTRUCTIONS),
            },
        )

    consistency = result.scores["consistency"]
    politeness = result.scores["politeness"]
    resolution = result.scores["resolution"]
    refund_promise = result.nouls["refund_promise"].noul

    # Each Score is on a 0-2 scale; average and stretch to the 1-10 rubric scale.
    avg = (consistency.score + politeness.score + resolution.score) / (2 * 3)
    score = round(1 + 9 * avg)

    problems = []
    if consistency.score < FAILING_LEVEL:
        problems.append("Reply is inconsistent with what the customer said.")
    if politeness.score < FAILING_LEVEL:
        problems.append("Reply is not sufficiently polite.")
    if resolution.score < FAILING_LEVEL:
        problems.append("Reply does not resolve the customer's issue.")
    if refund_promise > 0.5:
        problems.append("Reply promises a refund, which only billing may do.")
        score = min(score, 3)  # hard policy violation caps the score

    return {
        "score": max(1, min(10, score)),
        "problems": problems,
    }
