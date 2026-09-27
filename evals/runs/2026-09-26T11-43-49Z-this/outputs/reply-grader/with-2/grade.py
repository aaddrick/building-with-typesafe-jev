from typesafe_sdk import Noul, NoulCriteria, TypeSafeClient

MODEL = "jev-1.13.0"
NOUL_THRESHOLD = 0.5

QUESTIONS = {
    "consistent": Noul(
        instructions=(
            "Does everything `agent_reply` states about the customer's situation match "
            "what the customer actually said in `customer_message`, with no contradictions, "
            "invented facts, or misremembered details?"
        ),
        criteria=NoulCriteria(
            true="The reply's claims about the customer's situation match `customer_message`",
            false="The reply contradicts, invents, or misstates something the customer said",
        ),
    ),
    "polite": Noul(
        instructions="Is the tone of `agent_reply` polite and respectful toward the customer?",
        criteria=NoulCriteria(
            true="Courteous, respectful tone",
            false="Curt, dismissive, sarcastic, or rude tone",
        ),
    ),
    "resolves_issue": Noul(
        instructions=(
            "Does `agent_reply` resolve the issue the customer raised in `customer_message`, "
            "by providing a working solution, completing the requested action, or giving "
            "clear, complete next steps that fully address the request?"
        ),
        criteria=NoulCriteria(
            true="The issue is solved, or the customer knows exactly what will happen next",
            false="The issue is left open, deflected, or only partially addressed",
        ),
    ),
    "promises_refund": Noul(
        instructions="Does `agent_reply` promise, offer, or commit to giving the customer a refund?",
        criteria=NoulCriteria(
            true="The reply commits to, offers, or guarantees a refund",
            false="No refund is promised (declining, redirecting to billing, or not mentioning refunds)",
        ),
    ),
}

PROBLEM_MESSAGES = {
    "consistent": "Reply is inconsistent with what the customer said",
    "polite": "Reply is not polite",
    "resolves_issue": "Reply does not resolve the customer's issue",
    "promises_refund": "Reply promises a refund, which only billing may do",
}

_client = TypeSafeClient()


def grade(customer_message: str, agent_reply: str) -> dict:
    response = _client.system_one(
        state={"customer_message": customer_message, "agent_reply": agent_reply},
        questions=QUESTIONS,
        model=MODEL,
    )

    nouls = {key: response.nouls[key].noul for key in QUESTIONS}

    problems = [
        PROBLEM_MESSAGES[key]
        for key in ("consistent", "polite", "resolves_issue")
        if nouls[key] < NOUL_THRESHOLD
    ]
    if nouls["promises_refund"] >= NOUL_THRESHOLD:
        problems.append(PROBLEM_MESSAGES["promises_refund"])

    quality = (
        nouls["consistent"]
        + nouls["polite"]
        + nouls["resolves_issue"]
        + (1 - nouls["promises_refund"])
    ) / 4
    score = round(1 + 9 * quality, 1)

    return {
        "score": score,
        "problems": problems,
        "answers": nouls,
        "model": response.model,
    }
