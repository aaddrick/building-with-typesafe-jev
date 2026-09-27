"""Grade a support agent's reply against a fixed rubric using TypeSafe's Jev model."""

from typesafe_sdk import TypeSafeClient, Noul, NoulCriteria, Score

# Pinned so the hand-tuned thresholds below don't shift under us on a new release.
MODEL = "jev-1.13.0"

CONSISTENCY_LEVELS = [
    "The reply contradicts or misstates something the customer said",
    "The reply is mostly consistent but glosses over something the customer said",
    "The reply is fully consistent with what the customer said",
]
POLITENESS_LEVELS = [
    "The reply is rude, dismissive, or condescending",
    "The reply is neutral, neither warm nor rude",
    "The reply is polite and respectful",
]
RESOLUTION_LEVELS = [
    "The reply does not address the customer's issue (ignores it, deflects, or is a non-answer)",
    "The reply partially addresses the issue but leaves it unresolved or gives only a vague next step",
    "The reply gives a concrete fix, answer, or next step that resolves the issue",
]

QUESTIONS = {
    "consistency": Score(
        instructions="Is `agent_reply` consistent with what `customer_message` said?",
        criteria=CONSISTENCY_LEVELS,
    ),
    "politeness": Score(
        instructions="How polite is `agent_reply` toward the customer?",
        criteria=POLITENESS_LEVELS,
    ),
    "resolution": Score(
        instructions="Does `agent_reply` resolve the issue the customer raised in `customer_message`?",
        criteria=RESOLUTION_LEVELS,
    ),
    "refund_promise": Noul(
        instructions=(
            "Does `agent_reply` itself promise, guarantee, or commit to giving the customer "
            "a refund, rather than saying refunds are decided by billing or another team?"
        ),
        criteria=NoulCriteria(
            true="States or implies the customer will receive a refund or their money back",
            false="No refund commitment, or the decision is explicitly deferred to billing/another team",
        ),
    ),
}

# Rubric weights and cutoffs live here so they're easy to review and tune together.
SCORE_DIMENSIONS = ("consistency", "politeness", "resolution")
DIMENSION_WEIGHTS = {"consistency": 1.0, "politeness": 1.0, "resolution": 1.0}
LOW_SCORE_THRESHOLD = 0.5  # normalized dimension score below this is reported as a problem
REFUND_NOUL_THRESHOLD = 0.5  # noul above this counts as a refund promise
REFUND_VIOLATION_CAP = 3  # only billing may promise refunds, so this overrides a high rubric score


def grade(customer_message: str, agent_reply: str) -> dict:
    with TypeSafeClient() as client:
        response = client.system_one(
            state={"customer_message": customer_message, "agent_reply": agent_reply},
            questions=QUESTIONS,
            model=MODEL,
        )

    problems = []
    normalized = {}
    for dim in SCORE_DIMENSIONS:
        result = response.scores[dim]
        n_levels = len(result.legend)
        normalized[dim] = result.score / (n_levels - 1)
        if normalized[dim] < LOW_SCORE_THRESHOLD:
            dominant_level = max(result.probabilities, key=result.probabilities.get)
            problems.append(result.legend[dominant_level])

    refund_noul = response.nouls["refund_promise"].noul
    promises_refund = refund_noul > REFUND_NOUL_THRESHOLD
    if promises_refund:
        problems.append("Reply promises a refund; only Billing may promise refunds")

    weight_total = sum(DIMENSION_WEIGHTS.values())
    quality = sum(normalized[dim] * DIMENSION_WEIGHTS[dim] for dim in SCORE_DIMENSIONS) / weight_total
    score = 1 + round(quality * 9)
    if promises_refund:
        score = min(score, REFUND_VIOLATION_CAP)

    return {"score": score, "problems": problems}
