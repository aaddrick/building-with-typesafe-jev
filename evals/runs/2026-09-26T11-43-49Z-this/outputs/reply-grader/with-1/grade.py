"""Grade a support agent's reply against the team's rubric using Jev.

Requires: pip install typesafe-sdk   (or: uv add typesafe-sdk)
Requires: TYPESAFE_API_KEY set in the environment. Never pass the key in code.
"""

from typesafe_sdk import Noul, TypeSafeClient

# Pin the versioned model once thresholds below are tuned against it, e.g.
# "jev-1.13.0". Until then, ride the stable alias.
MODEL = "jev-latest"

# Noul above this leans "yes" to the question asked. 0.5 is Jev's "unsure" point;
# nudge per-question if a gold set shows a question runs systematically hot or cold.
PROBLEM_THRESHOLD = 0.5

# How much each rubric violation counts against the 1-10 score. The refund
# check is weighted heaviest: only the billing team may promise a refund, so a
# reply that does it is a policy violation, not just a quality slip.
WEIGHTS = {
    "inconsistent": 1.0,
    "impolite": 1.0,
    "unresolved": 1.0,
    "refund_promised": 2.0,
}

# One atomic, failure-oriented question per rubric item. Each is phrased so
# noul=1 means "this is a problem" -- that's what feeds both the problem list
# and the score, and it mirrors how the questions read.
QUESTIONS = {
    "inconsistent": Noul(
        instructions=(
            "Does the agent's reply in `agent_reply` contradict, misstate, or "
            "ignore something the customer clearly said in `customer_message`?"
        ),
    ),
    "impolite": Noul(
        instructions=(
            "Is the tone of the agent's reply in `agent_reply` impolite, curt, "
            "dismissive, or rude toward the customer?"
        ),
    ),
    "unresolved": Noul(
        instructions=(
            "Does the agent's reply in `agent_reply` fail to actually resolve or "
            "make concrete progress on the issue described in `customer_message`? "
            "Answer yes if it only acknowledges the problem, deflects, or tells "
            "the customer to go elsewhere without giving a fix."
        ),
    ),
    "refund_promised": Noul(
        instructions=(
            "Does the agent's reply in `agent_reply` promise, guarantee, or "
            "commit to issuing a refund to the customer? Only answer yes for an "
            "actual commitment, not a statement that billing will look into it."
        ),
    ),
}

PROBLEM_MESSAGES = {
    "inconsistent": "Reply is inconsistent with what the customer said.",
    "impolite": "Reply is not polite.",
    "unresolved": "Reply does not resolve the customer's issue.",
    "refund_promised": "Reply promises a refund; only billing may promise refunds.",
}

_client = None


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        _client = TypeSafeClient(model=MODEL)
    return _client


def grade(customer_message: str, agent_reply: str) -> dict:
    """Grade `agent_reply` against the support rubric.

    Returns {"score": int in [1, 10], "problems": [str, ...]}.
    """
    response = _get_client().system_one(
        state={"customer_message": customer_message, "agent_reply": agent_reply},
        questions=QUESTIONS,
    )

    nouls = {key: response.nouls[key].noul for key in QUESTIONS}

    problems = [
        PROBLEM_MESSAGES[key]
        for key in QUESTIONS
        if nouls[key] > PROBLEM_THRESHOLD
    ]

    total_weight = sum(WEIGHTS.values())
    badness = sum(WEIGHTS[key] * nouls[key] for key in QUESTIONS) / total_weight
    score = round(1 + 9 * (1 - badness))
    score = max(1, min(10, score))

    return {"score": score, "problems": problems}
