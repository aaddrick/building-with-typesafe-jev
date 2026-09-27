from typesafe_sdk import Noul, NoulCriteria, Score, TypeSafeClient

MODEL = "jev-1.13.0"

# Score levels describe situations, not degrees (best practice for Jev Score criteria).
CONSISTENCY_LEVELS = [
    "The reply contradicts, misstates, or ignores something the customer specifically said "
    "(e.g. addresses a different problem than described, or denies/reverses a fact the "
    "customer stated).",
    "The reply is broadly consistent with what the customer said but misses or glosses over "
    "a detail the customer mentioned.",
    "The reply is fully consistent with everything the customer stated, with no "
    "contradictions or omissions of stated facts.",
]

POLITENESS_LEVELS = [
    "Rude, dismissive, sarcastic, or blames the customer.",
    "Neutral and businesslike; no rudeness but little warmth (terse, robotic).",
    "Courteous and respectful throughout, acknowledging the customer's situation.",
]

RESOLUTION_LEVELS = [
    "Does not address the customer's problem at all, or only apologizes/deflects with no "
    "next step.",
    "Acknowledges the problem and gives a next step, but does not actually resolve it "
    "(vague promise to look into it, forwards elsewhere with no timeline, asks for "
    "information the customer already gave).",
    "Provides a concrete resolution, or a clear and specific actionable next step that "
    "addresses the customer's problem.",
]

REFUND_PROMISE_CRITERIA = NoulCriteria(
    true="Explicitly states a refund will be issued or processed, or guarantees money back.",
    false="No refund is promised; the reply may mention refunds in general or say it will "
    "forward the request to billing, without itself committing to one.",
)

# Equal weight per dimension in the composite 1-10 score. Tune here, not in the questions.
DIMENSION_WEIGHTS = {"consistency": 1 / 3, "politeness": 1 / 3, "resolution": 1 / 3}
DIMENSION_LEVELS = {
    "consistency": CONSISTENCY_LEVELS,
    "politeness": POLITENESS_LEVELS,
    "resolution": RESOLUTION_LEVELS,
}

REFUND_NOUL_THRESHOLD = 0.5
# An unauthorized refund promise is a compliance problem, not just a quality deduction:
# it caps the score regardless of how well the reply scored on everything else.
REFUND_VIOLATION_SCORE_CAP = 3


def grade(customer_message: str, agent_reply: str) -> dict:
    with TypeSafeClient() as client:
        response = client.system_one(
            state={"customer_message": customer_message, "agent_reply": agent_reply},
            model=MODEL,
            questions={
                "consistency": Score(
                    instructions=(
                        "How well does `agent_reply` align with the facts and requests "
                        "actually stated in `customer_message`?"
                    ),
                    criteria=CONSISTENCY_LEVELS,
                ),
                "politeness": Score(
                    instructions=(
                        "How polite and respectful is the tone of `agent_reply` toward the "
                        "customer?"
                    ),
                    criteria=POLITENESS_LEVELS,
                ),
                "resolution": Score(
                    instructions=(
                        "Does `agent_reply` actually resolve the problem described in "
                        "`customer_message`?"
                    ),
                    criteria=RESOLUTION_LEVELS,
                ),
                "promises_refund": Noul(
                    instructions=(
                        "Does `agent_reply` promise, guarantee, or commit to giving the "
                        "customer a monetary refund (as opposed to merely mentioning refunds "
                        "in general, or saying it will forward the request to the billing "
                        "team)?"
                    ),
                    criteria=REFUND_PROMISE_CRITERIA,
                ),
            },
        )

    problems = []
    weighted_norm = 0.0
    for dimension, levels in DIMENSION_LEVELS.items():
        raw_score = response.scores[dimension].score
        top_level = len(levels) - 1
        weighted_norm += DIMENSION_WEIGHTS[dimension] * (raw_score / top_level)

        nearest_level = min(round(raw_score), top_level)
        if nearest_level != top_level:
            problems.append(levels[nearest_level])

    promises_refund = response.nouls["promises_refund"].noul > REFUND_NOUL_THRESHOLD
    if promises_refund:
        problems.append(
            "Reply promises a refund, but only the billing team may promise refunds."
        )

    score = round(1 + 9 * weighted_norm)
    if promises_refund:
        score = min(score, REFUND_VIOLATION_SCORE_CAP)

    return {"score": score, "problems": problems}
