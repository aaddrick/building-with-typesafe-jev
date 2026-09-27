"""Grade a support agent's reply against a fixed rubric using TypeSafe's Jev model.

Consistency, politeness, and resolution are asked as Score questions (situational
levels, not vague "degrees") and combined into the numeric grade. Whether a refund
was promised is asked as a Noul because it's a yes/no gate, not a spectrum: any
promised refund is a rubric violation regardless of how well the reply otherwise
reads, since only the billing team may make that promise. `grade()` assumes the
replying agent is not on the billing team.
"""

from __future__ import annotations

from typesafe_sdk import Noul, Score, TypeSafeClient

# Pinned so that the constants below (weights, thresholds) stay valid even if
# "jev-latest" moves to a new model version later.
MODEL = "jev-1.13.0"

# How much each Score dimension counts toward the 1-10 grade. Weights need not sum to 1.
WEIGHTS = {
    "consistency": 0.3,
    "politeness": 0.2,
    "resolution": 0.5,
}

# A dimension's normalized score (0..1) below this bar is reported as a problem.
PROBLEM_THRESHOLDS = {
    "consistency": 0.75,  # anything short of "accurately reflects" is flagged
    "politeness": 0.5,    # rude is flagged; merely curt/neutral is not
    "resolution": 0.75,   # anything short of "fully resolves" is flagged
}

REFUND_NOUL_THRESHOLD = 0.5
REFUND_SCORE_CAP = 3  # a promised refund caps the grade regardless of other dimensions

QUESTIONS = {
    "consistency": Score(
        instructions=(
            "Compare `agent_reply` against `customer_message`. How consistent is "
            "the reply with what the customer actually said?"
        ),
        criteria=[
            "The reply contradicts or misstates something the customer said",
            "The reply neither confirms nor contradicts specific details the "
            "customer gave; it stays generic",
            "The reply accurately reflects the specific details the customer gave "
            "and does not contradict any of them",
        ],
    ),
    "politeness": Score(
        instructions="How polite is `agent_reply` toward the customer?",
        criteria=[
            "Rude, dismissive, or condescending toward the customer",
            "Neutral or curt, but not disrespectful",
            "Warm, courteous, and empathetic",
        ],
    ),
    "resolution": Score(
        instructions="Does `agent_reply` resolve the issue raised in `customer_message`?",
        criteria=[
            "Does not address the customer's issue at all",
            "Partially addresses the issue: leaves next steps unclear, or requires "
            "the customer to do more work without clear guidance",
            "Fully resolves the issue with a clear, actionable answer or fix",
        ],
    ),
    "refund_promise": Noul(
        instructions=(
            "Does `agent_reply` promise, guarantee, or commit to giving the "
            "customer a refund or money back?"
        ),
        criteria={
            "true": "States or implies a refund will be issued",
            "false": "No refund is promised (may discuss refund policy in general "
            "terms without committing to one)",
        },
    ),
}


def grade(customer_message: str, agent_reply: str) -> dict:
    """Grade `agent_reply` to `customer_message` on a 1-10 scale.

    Returns {"score": int, "problems": list[str], "model": str}.
    """
    state = {"customer_message": customer_message, "agent_reply": agent_reply}

    with TypeSafeClient() as client:
        response = client.system_one(state=state, questions=QUESTIONS, model=MODEL)

    scores = response.scores
    nouls = response.nouls

    normalized = {
        dim: scores[dim].score / (len(QUESTIONS[dim].criteria) - 1)
        for dim in ("consistency", "politeness", "resolution")
    }

    problems = []
    if normalized["consistency"] < PROBLEM_THRESHOLDS["consistency"]:
        problems.append("Reply is not consistent with what the customer said.")
    if normalized["politeness"] < PROBLEM_THRESHOLDS["politeness"]:
        problems.append("Reply is not polite.")
    if normalized["resolution"] < PROBLEM_THRESHOLDS["resolution"]:
        problems.append("Reply does not resolve the customer's issue.")

    refund_promised = nouls["refund_promise"].noul >= REFUND_NOUL_THRESHOLD
    if refund_promised:
        problems.append(
            "Reply promises a refund; only the billing team may promise refunds."
        )

    weighted = sum(WEIGHTS[dim] * normalized[dim] for dim in WEIGHTS)
    score = round(1 + 9 * weighted / sum(WEIGHTS.values()))
    if refund_promised:
        score = min(score, REFUND_SCORE_CAP)
    score = max(1, min(10, score))

    return {"score": score, "problems": problems, "model": response.model}
