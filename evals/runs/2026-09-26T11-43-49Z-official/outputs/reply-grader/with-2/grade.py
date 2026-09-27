from typesafe_sdk import Noul, Score, TypeSafeClient


def grade(customer_message: str, agent_reply: str) -> dict:
    state = {
        "customer_message": customer_message,
        "agent_reply": agent_reply,
    }

    with TypeSafeClient() as client:
        response = client.system_one(
            model="jev-latest",
            state=state,
            questions={
                "consistency": Score(
                    instructions=(
                        "How consistent is `agent_reply` with the facts and details "
                        "the customer stated in `customer_message`?"
                    ),
                    criteria=[
                        "Reply contradicts or ignores facts the customer stated, "
                        "or asserts things the customer never said",
                        "Reply mostly aligns but includes a minor inaccuracy or "
                        "unsupported assumption about what the customer said",
                        "Reply is fully consistent with everything the customer "
                        "stated, with no contradictions or fabrications",
                    ],
                ),
                "politeness": Score(
                    instructions=(
                        "How polite and respectful is the tone of `agent_reply` "
                        "toward the customer?"
                    ),
                    criteria=[
                        "Rude, dismissive, condescending, or likely to upset the customer",
                        "Neutral and professional but lacking warmth or empathy",
                        "Warm, courteous, and empathetic throughout",
                    ],
                ),
                "resolution": Score(
                    instructions=(
                        "How well does `agent_reply` resolve the issue raised in "
                        "`customer_message`?"
                    ),
                    criteria=[
                        "Does not address the issue, or leaves it unresolved with "
                        "no clear next step",
                        "Partially addresses the issue or gives a next step, but "
                        "does not fully resolve it",
                        "Fully resolves the issue or gives a complete, actionable "
                        "path to resolution",
                    ],
                ),
                "refund_promise": Noul(
                    instructions=(
                        "Does `agent_reply` promise, guarantee, or commit to giving "
                        "the customer a refund, rather than referring them to "
                        "billing or saying a refund may be possible?"
                    ),
                ),
            },
        )

    scores = response.scores
    problems: list[str] = []

    consistency_level = round(scores["consistency"].score)
    if consistency_level < 2:
        problems.append(
            "Reply is inconsistent with what the customer said"
            if consistency_level == 0
            else "Reply contains a minor inaccuracy about what the customer said"
        )

    politeness_level = round(scores["politeness"].score)
    if politeness_level < 2:
        problems.append(
            "Reply's tone is rude or dismissive"
            if politeness_level == 0
            else "Reply's tone is curt and lacks warmth"
        )

    resolution_level = round(scores["resolution"].score)
    if resolution_level < 2:
        problems.append(
            "Reply does not resolve the customer's issue"
            if resolution_level == 0
            else "Reply only partially resolves the customer's issue"
        )

    promises_refund = response.nouls["refund_promise"].noul >= 0.5
    if promises_refund:
        problems.append("Reply promises a refund; only Billing may promise refunds")

    # Each Score is 0-2; average and rescale to the 1-10 rubric scale.
    composite = (
        scores["consistency"].score + scores["politeness"].score + scores["resolution"].score
    ) / 6
    final_score = 1 + round(composite * 9)

    # A refund promise is a hard policy violation, not a gradient to average in.
    if promises_refund:
        final_score = min(final_score, 3)

    return {"score": final_score, "problems": problems}
