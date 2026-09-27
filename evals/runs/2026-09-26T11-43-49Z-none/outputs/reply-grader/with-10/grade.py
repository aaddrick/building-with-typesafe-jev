"""Grade a support agent's reply against our rubric using TypeSafe's Jev model."""

from typesafe_sdk import Noul, Score, TypeSafeClient

_CONSISTENCY_CRITERIA = [
    "Reply contradicts, ignores, or misstates a specific fact the customer stated",
    "Reply is broadly compatible with what the customer said but glosses over or blurs a detail",
    "Reply accurately reflects and directly engages with what the customer said",
]

_POLITENESS_CRITERIA = [
    "Reply is rude, dismissive, or uses language that could upset the customer",
    "Reply is neutral or curt but not disrespectful",
    "Reply is warm, courteous, and respectful throughout",
]

_RESOLUTION_CRITERIA = [
    "Reply does not address the customer's actual problem, or leaves it unresolved",
    "Reply partially addresses the problem, or gives a vague next step without a concrete fix",
    "Reply provides a concrete fix, action, or clear resolution to the customer's problem",
]

_MAX_LEVEL = len(_CONSISTENCY_CRITERIA) - 1  # all three rubrics use levels 0-2

# A Score below the midpoint of its rubric counts as failing that criterion.
_FAIL_THRESHOLD = _MAX_LEVEL / 2

_PROBLEM_MESSAGES = {
    "consistency": "Reply is not consistent with what the customer said.",
    "politeness": "Reply is not polite.",
    "resolution": "Reply does not resolve the customer's issue.",
    "refund_promise": "Reply promises a refund, which only billing may do.",
}


def grade(customer_message: str, agent_reply: str) -> dict:
    """Grade agent_reply 1-10 against our rubric, returning score and problems found."""
    state = {"customer_message": customer_message, "agent_reply": agent_reply}

    with TypeSafeClient(model="jev") as client:
        result = client.system_one(
            state=state,
            questions={
                "consistency": Score(
                    instructions=(
                        "How consistent the agent's reply is with what the customer "
                        "said in customer_message"
                    ),
                    criteria=_CONSISTENCY_CRITERIA,
                ),
                "politeness": Score(
                    instructions="How polite the agent's reply is toward the customer",
                    criteria=_POLITENESS_CRITERIA,
                ),
                "resolution": Score(
                    instructions="How fully the agent's reply resolves the customer's issue",
                    criteria=_RESOLUTION_CRITERIA,
                ),
                "refund_promise": Noul(
                    instructions=(
                        "The agent's reply promises, commits to, or guarantees the "
                        "customer a refund"
                    ),
                ),
            },
        )

    consistency = result.answers["consistency"].score
    politeness = result.answers["politeness"].score
    resolution = result.answers["resolution"].score
    refund_promised = result.answers["refund_promise"].noul > 0.5

    problems = []
    if consistency < _FAIL_THRESHOLD:
        problems.append(_PROBLEM_MESSAGES["consistency"])
    if politeness < _FAIL_THRESHOLD:
        problems.append(_PROBLEM_MESSAGES["politeness"])
    if resolution < _FAIL_THRESHOLD:
        problems.append(_PROBLEM_MESSAGES["resolution"])
    if refund_promised:
        problems.append(_PROBLEM_MESSAGES["refund_promise"])

    quality = (consistency + politeness + resolution) / (3 * _MAX_LEVEL)  # 0..1
    score = 1 + 9 * quality  # map to 1..10

    # An unauthorized refund promise is a hard rubric violation, independent of
    # how well the reply otherwise reads.
    if refund_promised:
        score = min(score, 3.0)

    return {
        "score": max(1, min(10, round(score))),
        "problems": problems,
    }
