"""Grade a support agent's reply against the team rubric using TypeSafe's Jev model."""

from typesafe_sdk import Noul, TypeSafeClient

_PROBLEM_THRESHOLD = 0.5

# Each check asks Jev to detect a *violation* of one rubric point. Framing the
# questions as "does this fail X" (rather than "does this satisfy X") lets a
# high noul probability map directly onto a problem to report.
_CHECKS = {
    "inconsistent": (
        "Does the agent's reply in `agent_reply` contradict, misstate, or "
        "ignore facts the customer stated in `customer_message`?",
        "Reply is inconsistent with what the customer said.",
    ),
    "impolite": (
        "Is the agent's reply in `agent_reply` impolite, rude, dismissive, "
        "or curt toward the customer?",
        "Reply is not polite.",
    ),
    "unresolved": (
        "Does the agent's reply in `agent_reply` fail to actually resolve or "
        "make concrete progress on the issue the customer raised in "
        "`customer_message` (for example by being vague, deflecting, or not "
        "addressing the request)?",
        "Reply does not resolve the customer's issue.",
    ),
    "promises_refund": (
        "Does the agent's reply in `agent_reply` promise, offer, or "
        "guarantee the customer a refund? This reply is from a general "
        "support agent, and only the billing team is authorized to promise "
        "refunds.",
        "Reply promises a refund, which only billing may do.",
    ),
}


def grade(customer_message: str, agent_reply: str) -> dict:
    """Score a support agent's reply from 1-10 against the team rubric.

    Returns {"score": int, "problems": list[str]}, where "problems" lists
    the rubric violations Jev found in the reply.
    """
    with TypeSafeClient() as client:
        response = client.system_one(
            model="jev-latest",
            state={
                "customer_message": customer_message,
                "agent_reply": agent_reply,
            },
            questions={
                key: Noul(instructions=instructions)
                for key, (instructions, _) in _CHECKS.items()
            },
        )

    problems = []
    pass_fractions = []
    for key, (_, problem_text) in _CHECKS.items():
        violation_probability = response.answers[key].noul
        pass_fractions.append(1 - violation_probability)
        if violation_probability > _PROBLEM_THRESHOLD:
            problems.append(problem_text)

    score = round(10 * sum(pass_fractions) / len(pass_fractions))
    score = max(1, min(10, score))

    return {"score": score, "problems": problems}
