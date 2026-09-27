from typesafe_sdk import Noul, Score, TypeSafeClient

# Score levels, lowest to highest. Index into these directly using the
# returned `score` (rounded) rather than trusting response legend shape.
_CONSISTENCY_LEVELS = [
    "Reply contradicts or ignores what the customer said, or responds to a different issue",
    "Reply is only loosely related to what the customer said and misses key details they mentioned",
    "Reply mostly matches what the customer said, with minor omissions or generalizations",
    "Reply directly and accurately reflects the specific details the customer described",
]

_POLITENESS_LEVELS = [
    "Rude, dismissive, or condescending tone",
    "Curt or impersonal tone lacking courtesy",
    "Generally polite tone with minor lapses in warmth or empathy",
    "Consistently courteous, empathetic, and respectful tone",
]

_RESOLUTION_LEVELS = [
    "Does not address the customer's problem or offer any next step",
    "Acknowledges the problem but gives no concrete solution or actionable next step",
    "Provides a partial solution or next step that may not fully resolve the issue",
    "Provides a clear, concrete solution or next step that fully resolves the issue",
]

_TOP_LEVEL = len(_CONSISTENCY_LEVELS) - 1  # levels are 4-wide (0-3) for all three Scores
_FLAG_BELOW = 2.0  # below "mostly/generally" level counts as a rubric problem


def _flag(label: str, levels: list[str], score: float) -> str | None:
    if score >= _FLAG_BELOW:
        return None
    level_index = max(0, min(_TOP_LEVEL, round(score)))
    return f"{label}: {levels[level_index]}"


def grade(customer_message: str, agent_reply: str) -> dict:
    with TypeSafeClient() as client:
        response = client.system_one(
            state={
                "customer_message": customer_message,
                "agent_reply": agent_reply,
            },
            questions={
                "consistency": Score(
                    instructions=(
                        "How consistent is `agent_reply` with what the customer "
                        "described in `customer_message`?"
                    ),
                    criteria=_CONSISTENCY_LEVELS,
                ),
                "politeness": Score(
                    instructions="How polite is the tone of `agent_reply`?",
                    criteria=_POLITENESS_LEVELS,
                ),
                "resolution": Score(
                    instructions=(
                        "How fully does `agent_reply` resolve the issue described "
                        "in `customer_message`?"
                    ),
                    criteria=_RESOLUTION_LEVELS,
                ),
                "refund_promise": Noul(
                    instructions=(
                        "Does `agent_reply` promise, guarantee, or commit that the "
                        "customer will receive a refund (as opposed to merely "
                        "acknowledging a refund request or saying billing will "
                        "review it)? The agent replying here is support, not "
                        "billing, and is not authorized to promise refunds."
                    ),
                ),
            },
        )

    consistency = response.scores["consistency"].score
    politeness = response.scores["politeness"].score
    resolution = response.scores["resolution"].score
    refund_promised = response.nouls["refund_promise"].noul >= 0.5

    problems = [
        p
        for p in (
            _flag("Consistency", _CONSISTENCY_LEVELS, consistency),
            _flag("Politeness", _POLITENESS_LEVELS, politeness),
            _flag("Resolution", _RESOLUTION_LEVELS, resolution),
        )
        if p is not None
    ]
    if refund_promised:
        problems.append(
            "Refund promise: reply promises a refund, but only Billing may "
            "promise refunds"
        )

    weighted_avg = (
        consistency / _TOP_LEVEL + politeness / _TOP_LEVEL + resolution / _TOP_LEVEL
    ) / 3
    raw_score = 1 + 9 * weighted_avg
    if refund_promised:
        raw_score = min(raw_score, 4)  # unauthorized refund promise is a serious violation

    score = max(1, min(10, round(raw_score)))

    return {"score": score, "problems": problems}
