"""Grade a support agent's reply against the support rubric using TypeSafe's Jev model."""

from __future__ import annotations

from typesafe_sdk import Noul, Score, TypeSafeClient

_CONSISTENCY_CRITERIA = [
    "Reply is inconsistent with or contradicts what the customer said, or addresses a different issue entirely",
    "Reply mostly ignores key details from the customer's message",
    "Reply loosely reflects the customer's message but misses or blurs some details",
    "Reply accurately reflects the customer's message with only minor omissions",
    "Reply is fully consistent with and accurately reflects everything the customer said",
]

_POLITENESS_CRITERIA = [
    "Rude, dismissive, or hostile tone",
    "Curt or impersonal tone",
    "Neutral, professional tone",
    "Polite and courteous tone",
    "Warm, empathetic, and highly professional tone",
]

_RESOLUTION_CRITERIA = [
    "Issue is not addressed at all",
    "Issue is acknowledged but no actionable resolution or next step is given",
    "Partial resolution or next steps are given, but the issue is not fully resolved",
    "Issue is resolved with only minor follow-up needed",
    "Issue is fully and clearly resolved",
]

# All criteria lists use the same 0-4 scale.
_TOP_LEVEL = len(_CONSISTENCY_CRITERIA) - 1
_FLAG_THRESHOLD = _TOP_LEVEL / 2  # below the neutral midpoint level

_WEIGHTS = {
    "consistency": 0.30,
    "politeness": 0.20,
    "resolution": 0.50,
}


def grade(customer_message: str, agent_reply: str) -> dict:
    """Grade `agent_reply` against `customer_message` on a 1-10 scale.

    Returns a dict with the overall `score` (1-10) and a `problems` list
    describing any rubric violations found.
    """
    with TypeSafeClient() as client:
        response = client.system_one(
            state={"customer_message": customer_message, "agent_reply": agent_reply},
            questions={
                "consistency": Score(
                    instructions=(
                        "How consistent and accurate is the agent's reply relative to what "
                        "the customer actually said in their message?"
                    ),
                    criteria=_CONSISTENCY_CRITERIA,
                ),
                "politeness": Score(
                    instructions="How polite and professional is the agent's reply?",
                    criteria=_POLITENESS_CRITERIA,
                ),
                "resolution": Score(
                    instructions="Does the agent's reply actually resolve the customer's issue?",
                    criteria=_RESOLUTION_CRITERIA,
                ),
                "refund_promised": Noul(
                    instructions=(
                        "Does the agent's reply promise, offer, or commit to giving the "
                        "customer a refund?"
                    ),
                ),
            },
        )

    answers = response.answers
    consistency = answers["consistency"].score
    politeness = answers["politeness"].score
    resolution = answers["resolution"].score
    refund_promised = answers["refund_promised"].noul >= 0.5

    problems = []
    if consistency < _FLAG_THRESHOLD:
        problems.append("Reply is not consistent with what the customer said.")
    if politeness < _FLAG_THRESHOLD:
        problems.append("Reply is not polite enough.")
    if resolution < _FLAG_THRESHOLD:
        problems.append("Reply does not resolve the customer's issue.")
    if refund_promised:
        problems.append(
            "Reply promises a refund; only Billing is authorized to promise refunds."
        )

    composite = (
        _WEIGHTS["consistency"] * (consistency / _TOP_LEVEL)
        + _WEIGHTS["politeness"] * (politeness / _TOP_LEVEL)
        + _WEIGHTS["resolution"] * (resolution / _TOP_LEVEL)
    )
    score = 1 + composite * 9  # map the 0-1 composite onto the 1-10 rubric scale
    if refund_promised:
        score = min(score, 4.0)  # policy violation caps the grade regardless of other scores

    return {
        "score": round(score, 1),
        "problems": problems,
    }
