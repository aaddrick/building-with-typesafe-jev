"""Grade support agent replies with TypeSafe's Jev model.

Requires the TYPESAFE_API_KEY environment variable to be set.
"""

from typesafe_sdk import Noul, Score, TypeSafeClient

_MODEL = "jev-latest"

# Shared 5-level rubric (0-4) for the three quality dimensions, describing
# concrete situations rather than degrees, as Jev's Score primitive expects.
_QUALITY_LEVELS = [
    "Completely fails on this dimension: badly wrong, rude, or unhelpful.",
    "Mostly fails: a problem serious enough to frustrate the customer.",
    "Partially succeeds: acceptable, but has a clear flaw a reviewer would flag.",
    "Mostly succeeds: minor room for improvement, nothing a customer would complain about.",
    "Fully succeeds: no flaws on this dimension.",
]
_MAX_LEVEL = len(_QUALITY_LEVELS) - 1


def grade(customer_message: str, agent_reply: str) -> dict:
    """Grade agent_reply against customer_message on a 1-10 scale.

    Checks: consistency with the customer's message, politeness, whether the
    issue is actually resolved, and whether a refund was improperly promised
    (only billing may promise refunds). Returns {"score": float, "problems": [str]}.
    """
    state = {
        "customer_message": customer_message,
        "agent_reply": agent_reply,
    }

    with TypeSafeClient() as client:
        response = client.system_one(
            state=state,
            questions={
                "consistency": Score(
                    instructions=(
                        "How consistent is `agent_reply` with what the customer "
                        "actually said in `customer_message`? Penalize any claim, "
                        "assumption, or detail in the reply that contradicts or "
                        "invents facts not present in the customer's message."
                    ),
                    criteria=_QUALITY_LEVELS,
                ),
                "politeness": Score(
                    instructions="How polite and professional is the tone of `agent_reply`?",
                    criteria=_QUALITY_LEVELS,
                ),
                "resolution": Score(
                    instructions=(
                        "How well does `agent_reply` actually resolve the issue the "
                        "customer raised in `customer_message`, rather than deflecting, "
                        "stalling, or leaving it open?"
                    ),
                    criteria=_QUALITY_LEVELS,
                ),
                "refund_promise": Noul(
                    instructions=(
                        "Does `agent_reply` promise, offer, guarantee, or commit to "
                        "issuing a refund to the customer? Only the billing team may "
                        "promise refunds, so any refund commitment from a support "
                        "agent is a policy violation."
                    ),
                ),
            },
            model=_MODEL,
        )

    consistency = response.scores["consistency"].score / _MAX_LEVEL
    politeness = response.scores["politeness"].score / _MAX_LEVEL
    resolution = response.scores["resolution"].score / _MAX_LEVEL
    refund_promised = response.nouls["refund_promise"].noul >= 0.5

    problems = []
    if consistency < 0.5:
        problems.append("Reply is inconsistent with what the customer said.")
    if politeness < 0.5:
        problems.append("Reply is not polite.")
    if resolution < 0.5:
        problems.append("Reply does not resolve the customer's issue.")
    if refund_promised:
        problems.append("Reply promises a refund, which only billing may promise.")

    quality = (consistency + politeness + resolution) / 3
    score = 1 + quality * 9
    if refund_promised:
        # Hard policy violation: cap the score regardless of otherwise-good quality.
        score = min(score, 3)

    return {"score": round(score, 1), "problems": problems}
