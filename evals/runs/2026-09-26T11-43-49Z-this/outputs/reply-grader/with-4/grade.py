"""Grade a support agent's reply against the team's rubric using TypeSafe's Jev model."""

import logging
from functools import lru_cache

from typesafe_sdk import Noul, NoulCriteria, Score, TypeSafeClient

logger = logging.getLogger(__name__)

MODEL = "jev-1.13.0"

CONSISTENCY_LEVELS = [
    "Contradicts or misstates a fact or request from `customer_message`",
    "Generic or only partially responsive to `customer_message`, but does not contradict it",
    "Accurately reflects the specific facts and requests in `customer_message`",
]

POLITENESS_LEVELS = [
    "Rude, dismissive, or hostile toward the customer",
    "Neutral or flat, neither warm nor rude",
    "Warm, respectful, and courteous",
]

RESOLUTION_LEVELS = [
    "Does not address the customer's issue or need in `customer_message` at all",
    "Acknowledges the issue but leaves it unresolved, e.g. vague next steps with no concrete action",
    "Provides a concrete resolution or a clear, actionable next step for the issue in `customer_message`",
]

# The three Score dimensions are weighted equally. A score below the middle
# level on any one of them is reported as a problem.
PROBLEM_THRESHOLD = 1.0
REFUND_NOUL_THRESHOLD = 0.5
# Promising an unauthorized refund is a policy violation, not just a quality
# deduction, so it caps the final score regardless of how the reply scores
# on the other dimensions.
REFUND_SCORE_CAP = 3


@lru_cache(maxsize=1)
def _client() -> TypeSafeClient:
    return TypeSafeClient(model=MODEL)


def grade(customer_message: str, agent_reply: str) -> dict:
    """Grade `agent_reply` against `customer_message` on a 1-10 scale.

    Checks: consistency with what the customer said, politeness, whether the
    issue is actually resolved, and whether the reply promises a refund
    (only billing may promise refunds, so any promise here is a problem).
    """
    response = _client().system_one(
        state={"customer_message": customer_message, "agent_reply": agent_reply},
        questions={
            "consistency": Score(
                instructions="How consistent is `agent_reply` with the facts and requests in `customer_message`?",
                criteria=CONSISTENCY_LEVELS,
            ),
            "politeness": Score(
                instructions="How polite is the tone of `agent_reply` toward the customer?",
                criteria=POLITENESS_LEVELS,
            ),
            "resolution": Score(
                instructions="Does `agent_reply` actually resolve the issue raised in `customer_message`?",
                criteria=RESOLUTION_LEVELS,
            ),
            "refund_promise": Noul(
                instructions=(
                    "Does `agent_reply` promise, offer, or commit to giving the "
                    "customer a refund, reimbursement, or credit?"
                ),
                criteria=NoulCriteria(
                    true="Explicitly offers, promises, or commits to a refund, reimbursement, or credit",
                    false="Does not commit to a refund; may mention policy or defer the decision without promising one",
                ),
            ),
        },
    )
    logger.debug("graded reply with %s", response.model)

    consistency = response.scores["consistency"].score
    politeness = response.scores["politeness"].score
    resolution = response.scores["resolution"].score
    refund_promise = response.nouls["refund_promise"].noul

    problems = []
    if consistency < PROBLEM_THRESHOLD:
        problems.append("Reply is inconsistent with what the customer said.")
    if politeness < PROBLEM_THRESHOLD:
        problems.append("Reply is not polite.")
    if resolution < PROBLEM_THRESHOLD:
        problems.append("Reply does not resolve the customer's issue.")
    if refund_promise >= REFUND_NOUL_THRESHOLD:
        problems.append("Reply promises a refund; only billing may promise refunds.")

    normalized = (
        consistency / (len(CONSISTENCY_LEVELS) - 1)
        + politeness / (len(POLITENESS_LEVELS) - 1)
        + resolution / (len(RESOLUTION_LEVELS) - 1)
    ) / 3
    score = round(1 + normalized * 9)
    if refund_promise >= REFUND_NOUL_THRESHOLD:
        score = min(score, REFUND_SCORE_CAP)

    return {"score": score, "problems": problems}
