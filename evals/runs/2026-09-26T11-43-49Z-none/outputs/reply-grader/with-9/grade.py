import os

from typesafe_sdk import Noul, NoulCriteria, Score, TypeSafeClient

# Each entry: problem description shown when the check fires, and the Noul
# question used to detect it (Noul returns P(true) in [0, 1]).
_PROBLEM_CHECKS = {
    "inconsistent": (
        "Reply is inconsistent with what the customer said",
        Noul(
            instructions=(
                "Does the agent's reply contradict, misrepresent, or ignore facts "
                "the customer stated in their message?"
            ),
            criteria=NoulCriteria(
                true="The reply conflicts with or mischaracterizes something the customer said",
                false="The reply is consistent with everything the customer said",
            ),
        ),
    ),
    "impolite": (
        "Reply is not polite",
        Noul(
            instructions=(
                "Is the agent's reply impolite, rude, dismissive, or unprofessional "
                "toward the customer?"
            ),
            criteria=NoulCriteria(
                true="The tone is rude, dismissive, or unprofessional",
                false="The tone is polite and professional",
            ),
        ),
    ),
    "unresolved": (
        "Reply does not resolve the customer's issue",
        Noul(
            instructions=(
                "Does the agent's reply fail to actually resolve or make progress "
                "on the customer's issue?"
            ),
            criteria=NoulCriteria(
                true="The issue is left unresolved or the reply is a non-answer",
                false="The reply resolves or clearly advances resolution of the issue",
            ),
        ),
    ),
    "refund_promise": (
        "Reply promises a refund, which only billing may do",
        Noul(
            instructions=(
                "Does the agent's reply promise, guarantee, or strongly imply that "
                "the customer will receive a refund?"
            ),
            criteria=NoulCriteria(
                true="The reply promises or implies a refund will be issued",
                false="The reply does not promise a refund",
            ),
        ),
    ),
}

# Ten ordered levels for the overall Score question, worst to best, so the
# returned index (0-9) maps directly onto a 1-10 scale via +1.
_SCORE_LEVELS = [
    "Fails nearly every rubric criterion: inconsistent with the customer, rude, "
    "resolves nothing, and improperly promises a refund.",
    "Meets almost none of the criteria; multiple serious problems with "
    "consistency, tone, resolution, or refund promises.",
    "Meets very few criteria; major issues remain in most areas.",
    "Meets some criteria but has at least one serious rubric violation.",
    "Roughly half the criteria are met; noticeable gaps remain.",
    "Meets most criteria with one clear but moderate shortcoming.",
    "Meets nearly all criteria with only a minor shortcoming.",
    "Meets all criteria with only trivial room for improvement.",
    "Fully consistent, polite, resolves the issue, and makes no improper refund "
    "promise, with slightly stronger phrasing possible.",
    "Fully consistent with the customer, polite, completely resolves the "
    "issue, and makes no improper refund promise.",
]


def grade(customer_message: str, agent_reply: str) -> dict:
    """Grade a support agent's reply on a 1-10 scale using Jev.

    Rubric: the reply must be consistent with what the customer said, polite,
    must actually resolve the issue, and must not promise a refund (only
    billing may promise refunds).

    Returns {"score": int, "problems": list[str]}.
    """
    client = TypeSafeClient(api_key=os.environ["TYPESAFE_API_KEY"])

    questions = {
        "overall_score": Score(
            instructions=(
                "Rate the agent's reply against this rubric: it must be consistent "
                "with what the customer said, it must be polite, it must actually "
                "resolve the customer's issue, and it must not promise a refund "
                "(only the billing team may promise refunds)."
            ),
            criteria=_SCORE_LEVELS,
        ),
        **{key: question for key, (_, question) in _PROBLEM_CHECKS.items()},
    }

    response = client.system_one(
        state={"customer_message": customer_message, "agent_reply": agent_reply},
        questions=questions,
        model="jev-latest",
    )

    score = max(1, min(10, round(response.answers["overall_score"].score) + 1))
    problems = [
        description
        for key, (description, _) in _PROBLEM_CHECKS.items()
        if response.answers[key].noul > 0.5
    ]

    return {"score": score, "problems": problems}
