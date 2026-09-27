"""Grade a support agent's reply against our rubric using TypeSafe's Jev model."""

from typesafe_sdk import Noul, TypeSafeClient

REFUND_CAP = 3  # max score allowed when the reply promises a refund
YES_THRESHOLD = 0.5


def grade(customer_message: str, agent_reply: str) -> dict:
    state = {"customer_message": customer_message, "agent_reply": agent_reply}

    with TypeSafeClient() as client:
        response = client.system_one(
            state=state,
            questions={
                "consistent": Noul(
                    instructions=(
                        "Does `agent_reply` stay factually consistent with what the "
                        "customer said in `customer_message`, with no contradictions "
                        "or misrepresentation of what the customer reported or asked for?"
                    ),
                    criteria={
                        "true": "The reply accurately reflects the customer's message with no contradictions or misstatements.",
                        "false": "The reply contradicts, misrepresents, or ignores facts the customer stated.",
                    },
                ),
                "polite": Noul(
                    instructions="Is `agent_reply` polite and respectful in tone toward the customer?",
                    criteria={
                        "true": "The reply is courteous and respectful.",
                        "false": "The reply is rude, dismissive, curt, or condescending.",
                    },
                ),
                "resolves": Noul(
                    instructions=(
                        "Does `agent_reply` actually resolve, or make concrete progress "
                        "resolving, the issue the customer describes in `customer_message`, "
                        "rather than being vague, deflecting, or non-committal?"
                    ),
                    criteria={
                        "true": "The reply gives a concrete resolution, fix, or next step that addresses the customer's issue.",
                        "false": "The reply is vague, deflects, or leaves the issue unaddressed.",
                    },
                ),
                "promises_refund": Noul(
                    instructions="Does `agent_reply` promise, offer, or commit to a refund for the customer?",
                    criteria={
                        "true": "The reply states or implies the customer will receive a refund, credit, or money back.",
                        "false": "The reply does not commit to a refund (it may direct the customer to billing without promising one).",
                    },
                ),
            },
        )

    consistent = response.nouls["consistent"].noul
    polite = response.nouls["polite"].noul
    resolves = response.nouls["resolves"].noul
    promises_refund = response.nouls["promises_refund"].noul

    problems = []
    if consistent < YES_THRESHOLD:
        problems.append("Reply is inconsistent with what the customer said.")
    if polite < YES_THRESHOLD:
        problems.append("Reply is not polite.")
    if resolves < YES_THRESHOLD:
        problems.append("Reply does not resolve the customer's issue.")
    if promises_refund >= YES_THRESHOLD:
        problems.append("Reply promises a refund, which only billing may do.")

    score = 1 + 9 * ((consistent + polite + resolves) / 3)
    if promises_refund >= YES_THRESHOLD:
        score = min(score, REFUND_CAP)
    score = max(1, min(10, round(score)))

    return {"score": score, "problems": problems}
