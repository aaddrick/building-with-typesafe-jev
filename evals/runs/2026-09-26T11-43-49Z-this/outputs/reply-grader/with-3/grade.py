"""Grade a support agent's reply against the team rubric using TypeSafe's Jev model."""

from typesafe_sdk import TypeSafeClient, Noul, NoulCriteria, Score

# Pinned so score thresholds below stay valid across model releases.
MODEL = "jev-1.13.0"

QUESTIONS = {
    "inconsistent": Noul(
        instructions=(
            "Does `agent_reply` state or imply anything that contradicts or "
            "misrepresents a fact the customer gave in `customer_message`?"
        ),
        criteria=NoulCriteria(
            true="The reply gets a fact, detail, or request from the customer wrong",
            false="The reply is consistent with everything the customer said",
        ),
    ),
    "promises_refund": Noul(
        instructions=(
            "Does `agent_reply` promise, offer, guarantee, or commit to giving "
            "the customer a refund?"
        ),
        criteria=NoulCriteria(
            true="The reply commits to a refund, credit, or money back",
            false="The reply does not commit to any refund",
        ),
    ),
    "politeness": Score(
        instructions="How polite and courteous is `agent_reply` toward the customer?",
        criteria=[
            "Rude, dismissive, or curt",
            "Neutral and professional, but impersonal",
            "Warm, courteous, and empathetic",
        ],
    ),
    "resolution": Score(
        instructions="Does `agent_reply` resolve the issue the customer raised in `customer_message`?",
        criteria=[
            "Does not address the customer's issue at all",
            "Acknowledges the issue but leaves it unresolved (e.g. only asks for more info or defers)",
            "Fully resolves the issue with a concrete answer or fix",
        ],
    ),
}

POLITENESS_LEVELS = 3
RESOLUTION_LEVELS = 3

# Composite weights: consistency and resolution matter more than tone alone.
WEIGHTS = {"consistency": 0.30, "politeness": 0.25, "resolution": 0.45}

# Starting points (per Jev's Noul-band guidance); tune on labeled examples.
NOUL_PROBLEM_THRESHOLD = 0.70
NOUL_REVIEW_THRESHOLD = 0.30
SCORE_PROBLEM_THRESHOLD = 1.0  # below the middle ("neutral" / "acknowledges") level


def grade(customer_message: str, agent_reply: str) -> dict:
    with TypeSafeClient() as client:
        response = client.system_one(
            state={"customer_message": customer_message, "agent_reply": agent_reply},
            questions=QUESTIONS,
            model=MODEL,
        )

    inconsistent = response.nouls["inconsistent"].noul
    promises_refund = response.nouls["promises_refund"].noul
    politeness = response.scores["politeness"].score
    resolution = response.scores["resolution"].score

    problems = []

    if inconsistent >= NOUL_PROBLEM_THRESHOLD:
        problems.append("Reply is inconsistent with what the customer said.")
    elif inconsistent >= NOUL_REVIEW_THRESHOLD:
        problems.append("Reply may be inconsistent with what the customer said (needs review).")

    if politeness < SCORE_PROBLEM_THRESHOLD:
        problems.append("Reply is not polite enough.")

    if resolution < SCORE_PROBLEM_THRESHOLD:
        problems.append("Reply does not resolve the customer's issue.")

    if promises_refund >= NOUL_PROBLEM_THRESHOLD:
        problems.append("Reply promises a refund; only Billing may promise refunds.")
    elif promises_refund >= NOUL_REVIEW_THRESHOLD:
        problems.append(
            "Reply may promise a refund (needs review); only Billing may promise refunds."
        )

    weighted = (
        WEIGHTS["consistency"] * (1 - inconsistent)
        + WEIGHTS["politeness"] * (politeness / (POLITENESS_LEVELS - 1))
        + WEIGHTS["resolution"] * (resolution / (RESOLUTION_LEVELS - 1))
    )
    score = round(1 + 9 * weighted)

    # A refund promise is a hard rubric violation regardless of the other dimensions.
    if promises_refund >= NOUL_PROBLEM_THRESHOLD:
        score = min(score, 3)

    score = max(1, min(10, score))

    return {"score": score, "problems": problems}
