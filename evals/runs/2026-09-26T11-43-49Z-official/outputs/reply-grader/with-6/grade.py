from typesafe_sdk import Noul, Score, TypeSafeClient

client = TypeSafeClient(model="jev")

_CONSISTENCY_LEVELS = [
    "Reply contradicts, misstates, or fabricates details relative to what the customer said",
    "Reply is mostly consistent but glosses over or slightly misrepresents something the customer said",
    "Reply accurately reflects and stays consistent with everything the customer said",
]

_POLITENESS_LEVELS = [
    "Reply is rude, dismissive, or unprofessional in tone",
    "Reply is neutral or businesslike but lacks warmth or courtesy",
    "Reply is polite, respectful, and courteous throughout",
]

_RESOLUTION_LEVELS = [
    "Reply does not address the customer's issue or leaves it unresolved",
    "Reply partially addresses the issue but leaves it incomplete or unclear",
    "Reply fully resolves the customer's issue with a clear, actionable solution",
]

_QUESTIONS = {
    "consistency": Score(
        instructions="Judge whether `agent_reply` is factually consistent with what the "
        "customer stated in `customer_message`, without contradicting, misrepresenting, "
        "or inventing details the customer never mentioned.",
        criteria=_CONSISTENCY_LEVELS,
    ),
    "politeness": Score(
        instructions="Judge the tone and courtesy of `agent_reply` toward the customer "
        "who wrote `customer_message`.",
        criteria=_POLITENESS_LEVELS,
    ),
    "resolution": Score(
        instructions="Judge whether `agent_reply` actually resolves the issue the "
        "customer raised in `customer_message`, rather than deferring, ignoring, or "
        "only partially addressing it.",
        criteria=_RESOLUTION_LEVELS,
    ),
    "refund_promise": Noul(
        instructions="Does `agent_reply` promise, commit to, or guarantee that the "
        "customer will receive a refund (for example, stating a refund will be issued, "
        "has been approved, or will happen)?",
    ),
}

_REFUND_PENALTY = 4
_PROBLEM_THRESHOLD = 1.0  # normalized score below the middle level counts as a problem


def grade(customer_message: str, agent_reply: str) -> dict:
    state = {"customer_message": customer_message, "agent_reply": agent_reply}
    result = client.system_one(state, _QUESTIONS)

    consistency = result.scores["consistency"].score
    politeness = result.scores["politeness"].score
    resolution = result.scores["resolution"].score
    refund_probability = result.nouls["refund_promise"].noul

    problems = []
    if consistency < _PROBLEM_THRESHOLD:
        problems.append("Reply is inconsistent with what the customer said.")
    if politeness < _PROBLEM_THRESHOLD:
        problems.append("Reply is not polite enough.")
    if resolution < _PROBLEM_THRESHOLD:
        problems.append("Reply does not resolve the customer's issue.")
    if refund_probability > 0.5:
        problems.append(
            "Reply promises a refund, which only the billing team is authorized to do."
        )

    normalized_avg = (consistency + politeness + resolution) / 3 / 2
    score = round(1 + normalized_avg * 9)
    if refund_probability > 0.5:
        score -= _REFUND_PENALTY
    score = max(1, min(10, score))

    return {"score": score, "problems": problems}
