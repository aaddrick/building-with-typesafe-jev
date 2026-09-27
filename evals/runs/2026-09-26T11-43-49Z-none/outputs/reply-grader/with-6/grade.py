"""Grade a support agent's reply against our response rubric using typesafe.ai's Jev model."""

from typesafe_sdk import Noul, NoulCriteria, Score, TypeSafeClient

# Overall quality levels, worst to best, used to produce the 1-10 score.
_QUALITY_LEVELS = [
    "Reply contradicts what the customer said, is rude, fails to resolve the "
    "issue, and/or promises a refund it has no authority to promise",
    "Reply has a serious problem: it misrepresents the customer's message, is "
    "impolite, or leaves the issue unresolved",
    "Reply is on-topic and polite but only partially resolves the issue, or is "
    "vague about next steps",
    "Reply is polite, consistent with the customer's message, and resolves the "
    "issue, with minor room for improvement",
    "Reply is polite, fully consistent with the customer's message, clearly "
    "resolves the issue, and stays within the agent's authority (no "
    "unauthorized refund promises)",
]

# One Noul (yes/no) question per rubric criterion.
_NOUL_QUESTIONS = {
    "consistent": Noul(
        instructions=(
            "Is the agent's reply consistent with what the customer actually "
            "said, without contradicting or fabricating details?"
        ),
        criteria=NoulCriteria(
            true="The reply accurately reflects the customer's message and "
            "doesn't invent or contradict details",
            false="The reply misstates, ignores, or contradicts something the "
            "customer said",
        ),
    ),
    "polite": Noul(
        instructions="Is the agent's reply polite and respectful in tone?",
        criteria=NoulCriteria(
            true="The reply is courteous, respectful, and professional",
            false="The reply is curt, dismissive, rude, or otherwise impolite",
        ),
    ),
    "resolves_issue": Noul(
        instructions=(
            "Does the agent's reply actually resolve the customer's issue (or "
            "give a clear, actionable path to resolution)?"
        ),
        criteria=NoulCriteria(
            true="The issue is resolved, or the customer is given clear, "
            "actionable next steps that resolve it",
            false="The issue is left unresolved, deflected, or the reply is "
            "vague about what happens next",
        ),
    ),
    "promises_refund": Noul(
        instructions="Does the agent's reply promise the customer a refund?",
        criteria=NoulCriteria(
            true="The reply commits to, guarantees, or states that a refund "
            "will happen",
            false="The reply does not promise a refund (it may mention "
            "escalating to billing, but doesn't promise the outcome)",
        ),
    ),
}

_PROBLEM_MESSAGES = {
    "consistent": "Reply is not consistent with what the customer said.",
    "polite": "Reply is not polite.",
    "resolves_issue": "Reply does not resolve the customer's issue.",
    "promises_refund": "Reply promises a refund, which only billing may promise.",
}

_THRESHOLD = 0.5


def grade(customer_message: str, agent_reply: str) -> dict:
    """Grade a support agent's reply on a 1-10 scale using typesafe.ai's Jev model.

    Checks the reply against our rubric: it must be consistent with what the
    customer said, polite, actually resolve the issue, and not promise a
    refund (only billing may promise refunds).

    Returns a dict with:
        score: float from 1 to 10.
        problems: list of rubric violations found, if any.
    """
    state = {
        "customer_message": customer_message,
        "agent_reply": agent_reply,
    }

    questions = dict(_NOUL_QUESTIONS)
    questions["overall_quality"] = Score(
        instructions=(
            "Rate the agent's reply against the support rubric: it should be "
            "consistent with what the customer said, polite, resolve the "
            "issue, and not promise a refund (only billing may promise "
            "refunds)."
        ),
        criteria=_QUALITY_LEVELS,
    )

    with TypeSafeClient() as client:
        response = client.system_one(state=state, questions=questions)

    problems = []
    for key in _NOUL_QUESTIONS:
        value = response.nouls[key].noul
        is_problem = (
            value > _THRESHOLD if key == "promises_refund" else value < _THRESHOLD
        )
        if is_problem:
            problems.append(_PROBLEM_MESSAGES[key])

    top_level = len(_QUALITY_LEVELS) - 1
    raw_score = response.scores["overall_quality"].score  # 0..top_level
    score = round(1 + (raw_score / top_level) * 9, 1)  # map to 1..10

    return {
        "score": score,
        "problems": problems,
    }
