"""Grade a support agent's reply using typesafe.ai's Jev model.

Rubric:
  - The reply is consistent with what the customer said.
  - The reply is polite.
  - The reply actually resolves the issue.
  - The reply does not promise a refund (only billing may promise refunds).
"""

from typesafe_sdk import Noul, Score, TypeSafeClient

REFUND_PROMISE_THRESHOLD = 0.5

# Each Score rubric has 4 ordered levels (0-3); normalize by dividing by 3.
_SCORE_CRITERIA = {
    "consistency": [
        "Reply contradicts or misrepresents facts the customer stated",
        "Reply ignores or is only loosely related to what the customer said",
        "Reply is mostly consistent, with minor omissions",
        "Reply is fully consistent and accurately reflects what the customer said",
    ],
    "politeness": [
        "Rude, dismissive, or hostile tone",
        "Curt or cold, lacking basic courtesy",
        "Generally polite, with minor lapses",
        "Consistently courteous and respectful",
    ],
    "resolution": [
        "Does not address the customer's issue at all",
        "Acknowledges the issue but offers no actionable resolution",
        "Offers a partial resolution or next steps, but the issue isn't fully resolved",
        "Fully resolves the customer's issue",
    ],
}

_SCORE_INSTRUCTIONS = {
    "consistency": (
        "Does the agent's reply (`agent_reply`) accurately reflect and stay "
        "consistent with what the customer said (`customer_message`), without "
        "contradicting or misrepresenting it?"
    ),
    "politeness": "How polite is the agent's reply (`agent_reply`)?",
    "resolution": (
        "Does the agent's reply (`agent_reply`) actually resolve the "
        "customer's issue described in `customer_message`?"
    ),
}

_LOW_SCORE_LEVEL_THRESHOLD = 1  # flag the bottom two of four levels (0, 1)


def grade(customer_message: str, agent_reply: str) -> dict:
    client = TypeSafeClient()
    try:
        state = {"customer_message": customer_message, "agent_reply": agent_reply}
        response = client.system_one(
            state=state,
            questions={
                "consistency": Score(
                    instructions=_SCORE_INSTRUCTIONS["consistency"],
                    criteria=_SCORE_CRITERIA["consistency"],
                ),
                "politeness": Score(
                    instructions=_SCORE_INSTRUCTIONS["politeness"],
                    criteria=_SCORE_CRITERIA["politeness"],
                ),
                "resolution": Score(
                    instructions=_SCORE_INSTRUCTIONS["resolution"],
                    criteria=_SCORE_CRITERIA["resolution"],
                ),
                "promises_refund": Noul(
                    instructions=(
                        "The agent's reply (`agent_reply`) promises, guarantees, "
                        "or commits to issuing a refund to the customer."
                    ),
                ),
            },
        )
    finally:
        client.close()

    problems = []
    normalized_scores = []

    for key in ("consistency", "politeness", "resolution"):
        answer = response.answers[key]
        num_levels = len(_SCORE_CRITERIA[key])
        normalized_scores.append(answer.score / (num_levels - 1))

        nearest_level = round(answer.score)
        if nearest_level <= _LOW_SCORE_LEVEL_THRESHOLD:
            problems.append(f"{key}: {answer.legend[nearest_level]}")

    final_score = 1 + (sum(normalized_scores) / len(normalized_scores)) * 9

    if response.answers["promises_refund"].noul > REFUND_PROMISE_THRESHOLD:
        problems.append(
            "Reply promises a refund, but only billing may promise refunds."
        )
        final_score = max(1.0, final_score - 3)

    return {"score": round(final_score, 1), "problems": problems}
