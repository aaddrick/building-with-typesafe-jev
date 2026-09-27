from typesafe_sdk import Noul, TypeSafeClient


def grade(customer_message: str, agent_reply: str) -> dict:
    """Grade a support agent's reply 1-10 against the rubric, returning problems found."""
    with TypeSafeClient() as client:
        result = client.system_one(
            state={"customer_message": customer_message, "agent_reply": agent_reply},
            questions={
                "consistent": Noul(
                    instructions=(
                        "Does `agent_reply` accurately reflect what the customer said in "
                        "`customer_message`, without contradicting, misstating, or ignoring "
                        "key facts the customer gave?"
                    ),
                    criteria={
                        "true": "The reply's account of the situation matches what the customer described",
                        "false": "The reply contradicts, misstates, or ignores key facts the customer gave",
                    },
                ),
                "polite": Noul(
                    instructions=(
                        "Is `agent_reply` polite, respectful, and professional in tone "
                        "toward the customer?"
                    ),
                    criteria={
                        "true": "Courteous, respectful, professional tone",
                        "false": "Rude, dismissive, curt, or unprofessional tone",
                    },
                ),
                "resolves_issue": Noul(
                    instructions=(
                        "Does `agent_reply` actually resolve the customer's issue described "
                        "in `customer_message`, by giving a concrete fix, answer, or clear "
                        "next step, rather than being vague or deflecting?"
                    ),
                    criteria={
                        "true": "Provides a concrete solution, fix, or clear actionable next step",
                        "false": "Vague, deflects, or leaves the issue unresolved",
                    },
                ),
                "promises_refund": Noul(
                    instructions=(
                        "Does `agent_reply` promise, guarantee, or commit that the customer "
                        "will receive a refund? Referring the customer to the billing team "
                        "to request or process a refund is NOT promising a refund."
                    ),
                    criteria={
                        "true": "The agent directly commits to giving the customer a refund",
                        "false": "No refund is promised, or the agent only refers the customer to billing",
                    },
                ),
            },
        )

    consistent = result.nouls["consistent"].noul
    polite = result.nouls["polite"].noul
    resolves_issue = result.nouls["resolves_issue"].noul
    promises_refund = result.nouls["promises_refund"].noul

    problems = []
    if consistent < 0.5:
        problems.append("Reply is inconsistent with what the customer said.")
    if polite < 0.5:
        problems.append("Reply is not polite.")
    if resolves_issue < 0.5:
        problems.append("Reply does not resolve the customer's issue.")
    if promises_refund >= 0.5:
        problems.append("Reply promises a refund, which only Billing may authorize.")

    weighted = (
        0.25 * consistent
        + 0.20 * polite
        + 0.35 * resolves_issue
        + 0.20 * (1 - promises_refund)
    )
    score = round(1 + 9 * weighted, 1)

    return {"score": score, "problems": problems}
