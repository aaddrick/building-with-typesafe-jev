from typesafe_sdk import TypeSafeClient, Score, Noul

# Score levels: tune wording/count on labeled data before changing thresholds below.
CONSISTENCY_LEVELS = [
    "Reply contradicts or misstates specific facts the customer stated",
    "Reply is vague or omits details the customer gave, but does not contradict them",
    "Reply accurately reflects the specific facts and details the customer stated",
]
POLITENESS_LEVELS = [
    "Reply is curt, dismissive, or contains rude or impatient language",
    "Reply is neutral in tone, neither warm nor rude",
    "Reply is courteous and respectful throughout",
]
RESOLUTION_LEVELS = [
    "Does not address the customer's issue at all",
    "Acknowledges the issue but offers no solution or actionable next step",
    "Offers a partial solution or an incomplete next step",
    "Fully resolves the issue or gives a clear, complete next step",
]

# Composite scoring weights (composite_scoring pattern), must sum to 1.0.
WEIGHTS = {"consistency": 0.25, "politeness": 0.20, "resolution": 0.55}

# round(score) at or below these levels counts as a rubric failure.
CONSISTENCY_FAIL_LEVEL = 0
POLITENESS_FAIL_LEVEL = 0
RESOLUTION_FAIL_LEVEL = 1
REFUND_PROMISE_THRESHOLD = 0.5

# Pin the version once thresholds above are tuned against real answers.
MODEL = "jev-latest"


def grade(customer_message: str, agent_reply: str) -> dict:
    """Grade a support agent's reply 1-10 against the rubric.

    Returns {"score": int, "problems": list[str], "model": str}.
    """
    state = {"customer_message": customer_message, "agent_reply": agent_reply}

    with TypeSafeClient() as client:
        r = client.system_one(
            state,
            {
                "consistency": Score(
                    instructions=(
                        "Is `agent_reply` consistent with the facts and details "
                        "`customer_message` states, without contradicting or "
                        "misrepresenting them?"
                    ),
                    criteria=CONSISTENCY_LEVELS,
                ),
                "politeness": Score(
                    instructions="How polite and respectful is the tone of `agent_reply`?",
                    criteria=POLITENESS_LEVELS,
                ),
                "resolution": Score(
                    instructions=(
                        "Does `agent_reply` actually resolve the issue raised in "
                        "`customer_message`, as opposed to just acknowledging it?"
                    ),
                    criteria=RESOLUTION_LEVELS,
                ),
                "refund_promise": Noul(
                    instructions=(
                        "Does `agent_reply` promise, guarantee, or commit to giving "
                        "the customer a refund, as opposed to merely explaining "
                        "policy or routing the customer to billing?"
                    ),
                ),
            },
            model=MODEL,
        )

    consistency = r.scores["consistency"]
    politeness = r.scores["politeness"]
    resolution = r.scores["resolution"]
    refund_promise = r.nouls["refund_promise"].noul

    problems = []
    if round(consistency.score) <= CONSISTENCY_FAIL_LEVEL:
        problems.append("Reply is inconsistent with what the customer said.")
    if round(politeness.score) <= POLITENESS_FAIL_LEVEL:
        problems.append("Reply is not polite.")
    if round(resolution.score) <= RESOLUTION_FAIL_LEVEL:
        problems.append("Reply does not resolve the customer's issue.")
    if refund_promise > REFUND_PROMISE_THRESHOLD:
        problems.append("Reply promises a refund, which only billing may do.")

    weighted = (
        WEIGHTS["consistency"] * (consistency.score / (len(CONSISTENCY_LEVELS) - 1))
        + WEIGHTS["politeness"] * (politeness.score / (len(POLITENESS_LEVELS) - 1))
        + WEIGHTS["resolution"] * (resolution.score / (len(RESOLUTION_LEVELS) - 1))
    )
    score = round(1 + 9 * weighted)

    # Hard policy violation: cap the score no matter how good the rest of the reply is.
    if refund_promise > REFUND_PROMISE_THRESHOLD:
        score = min(score, 3)

    return {
        "score": max(1, min(10, score)),
        "problems": problems,
        "model": r.model,
    }
