"""Grade a support agent's reply against a fixed rubric using TypeSafe's Jev model."""

from typesafe_sdk import Noul, Score, TypeSafeClient

_CONSISTENCY_CRITERIA = [
    "Reply contradicts or misrepresents facts the customer stated, or responds to a different issue entirely",
    "Reply mostly addresses the customer's issue but includes inaccurate or fabricated details about what the customer said",
    "Reply is consistent with the customer's message, with only minor imprecision",
    "Reply is fully accurate and consistent with everything the customer stated",
]

_POLITENESS_CRITERIA = [
    "Rude, dismissive, or hostile tone",
    "Curt or cold, lacking courtesy",
    "Polite and professional, if somewhat generic",
    "Warm, empathetic, and professional throughout",
]

_RESOLUTION_CRITERIA = [
    "Does not address the issue or offers no actionable help",
    "Acknowledges the issue but leaves it unresolved, or defers without a concrete next step",
    "Provides a concrete step that resolves the issue or clearly moves it forward",
    "Fully and clearly resolves the customer's issue",
]

# All three Score rubrics above share this top level, so one constant normalizes them.
_TOP_LEVEL = len(_CONSISTENCY_CRITERIA) - 1
_PROBLEM_THRESHOLD = 2.0  # below this (out of _TOP_LEVEL) on a dimension is a problem
_REFUND_PENALTY = 4.0


def grade(customer_message: str, agent_reply: str) -> dict:
    """Grade a support agent's reply on a 1-10 scale using Jev.

    Checks that the reply (1) is consistent with what the customer said,
    (2) is polite, (3) resolves the issue, and (4) does not promise a
    refund, since only the billing team may promise refunds.

    Returns a dict with "score" (1-10) and "problems" (list of str).
    """
    with TypeSafeClient() as client:
        result = client.system_one(
            state={"customer_message": customer_message, "agent_reply": agent_reply},
            questions={
                "consistency": Score(
                    instructions=(
                        "How consistent is the agent_reply with what the customer "
                        "actually said in customer_message?"
                    ),
                    criteria=_CONSISTENCY_CRITERIA,
                ),
                "politeness": Score(
                    instructions="How polite and professional is the agent_reply's tone?",
                    criteria=_POLITENESS_CRITERIA,
                ),
                "resolution": Score(
                    instructions="Does the agent_reply actually resolve the customer's issue?",
                    criteria=_RESOLUTION_CRITERIA,
                ),
                "refund_promise": Noul(
                    instructions=(
                        "Does the agent_reply promise, offer, or commit to issuing "
                        "the customer a refund?"
                    ),
                ),
            },
        )

    consistency = result.scores["consistency"]
    politeness = result.scores["politeness"]
    resolution = result.scores["resolution"]
    refund_promise = result.nouls["refund_promise"]

    quality = (
        consistency.score / _TOP_LEVEL
        + politeness.score / _TOP_LEVEL
        + resolution.score / _TOP_LEVEL
    ) / 3
    score = 1 + 9 * quality

    problems = []
    if consistency.score < _PROBLEM_THRESHOLD:
        problems.append("Reply is not fully consistent with what the customer said.")
    if politeness.score < _PROBLEM_THRESHOLD:
        problems.append("Reply is not polite enough.")
    if resolution.score < _PROBLEM_THRESHOLD:
        problems.append("Reply does not resolve the customer's issue.")
    if refund_promise.noul >= 0.5:
        problems.append(
            "Reply promises a refund; only the billing team may promise refunds."
        )
        score -= _REFUND_PENALTY

    score = max(1.0, min(10.0, score))

    return {"score": round(score, 1), "problems": problems}
