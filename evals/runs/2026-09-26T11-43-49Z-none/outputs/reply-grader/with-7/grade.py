from typesafe_sdk import Noul, TypeSafeClient

# Each criterion is phrased so that `noul` near 1.0 means "criterion holds".
_CRITERIA = {
    "consistent": Noul(
        instructions=(
            "The agent's reply is consistent with what the customer said: it does not "
            "misstate, ignore, or contradict any fact or request from the customer's message."
        ),
    ),
    "polite": Noul(
        instructions="The agent's reply is polite and respectful in tone.",
    ),
    "resolves_issue": Noul(
        instructions=(
            "The agent's reply actually resolves the customer's issue, or gives a clear, "
            "actionable next step that resolves it."
        ),
    ),
    "promises_refund": Noul(
        instructions=(
            "The agent's reply promises, offers, commits to, or guarantees a refund to the "
            "customer."
        ),
        criteria=(
            "Yes: any language promising, offering, or guaranteeing money back. "
            "No: no refund is promised (mentioning billing/refund policy without "
            "committing to one does not count)."
        ),
    ),
}

_PROBLEM_MESSAGES = {
    "consistent": "Reply is inconsistent with what the customer said.",
    "polite": "Reply is not polite.",
    "resolves_issue": "Reply does not resolve the customer's issue.",
    "promises_refund": "Reply promises a refund, which only billing may do.",
}

_THRESHOLD = 0.5
_REFUND_PROMISE_CAP = 3.0


def grade(customer_message: str, agent_reply: str) -> dict:
    state = f"Customer message:\n{customer_message}\n\nAgent reply:\n{agent_reply}"

    with TypeSafeClient() as client:
        response = client.system_one(state=state, questions=_CRITERIA)

    nouls = {key: response.answers[key].noul for key in _CRITERIA}

    problems = [
        _PROBLEM_MESSAGES[key]
        for key in ("consistent", "polite", "resolves_issue")
        if nouls[key] < _THRESHOLD
    ]
    refund_promised = nouls["promises_refund"] >= _THRESHOLD
    if refund_promised:
        problems.append(_PROBLEM_MESSAGES["promises_refund"])

    positive = (nouls["consistent"] + nouls["polite"] + nouls["resolves_issue"]) / 3
    score = 1 + 9 * positive
    if refund_promised:
        score = min(score, _REFUND_PROMISE_CAP)
    score = round(max(1.0, min(10.0, score)), 1)

    return {"score": score, "problems": problems}
