"""Grade a support agent's reply using typesafe.ai's Jev model.

Requires the TYPESAFE_API_KEY environment variable to be set.
"""

from typesafe_sdk import Noul, TypeSafeClient

# Below this probability, a Noul judgment is treated as "no".
_THRESHOLD = 0.5


def grade(customer_message: str, agent_reply: str) -> dict:
    """Grade `agent_reply` against the support rubric for `customer_message`.

    Returns a dict with:
      - "score": overall quality on a 1-10 scale
      - "problems": list of rubric violations found, if any
    """
    state = {"customer_message": customer_message, "agent_reply": agent_reply}
    questions = {
        "consistent": Noul(
            instructions=(
                "Is the agent's reply in `agent_reply` consistent with what the "
                "customer said in `customer_message` (it accurately reflects their "
                "situation and request, without contradicting or misrepresenting it)?"
            ),
            criteria={
                "true": "The reply accurately reflects the customer's message",
                "false": "The reply contradicts, ignores, or misrepresents what the customer said",
            },
        ),
        "polite": Noul(
            instructions="Is the agent's reply in `agent_reply` polite and respectful toward the customer?",
            criteria={
                "true": "The tone is courteous and respectful",
                "false": "The tone is rude, dismissive, curt, or otherwise disrespectful",
            },
        ),
        "resolves": Noul(
            instructions=(
                "Does the agent's reply in `agent_reply` resolve the customer's issue "
                "described in `customer_message`, by giving a clear solution, answer, "
                "or concrete next step?"
            ),
            criteria={
                "true": "The reply provides a clear resolution or concrete next step",
                "false": "The reply is vague, deflects, or leaves the issue unaddressed",
            },
        ),
        "promises_refund": Noul(
            instructions=(
                "Does the agent's reply in `agent_reply` promise, offer, or commit to "
                "issuing a refund to the customer? Only the billing team may promise a "
                "refund, and this agent is not on the billing team."
            ),
            criteria={
                "true": "The reply promises, offers, or commits to a refund",
                "false": "The reply does not promise or commit to a refund",
            },
        ),
    }

    with TypeSafeClient() as client:
        result = client.system_one(state, questions)

    consistent = result.nouls["consistent"].noul
    polite = result.nouls["polite"].noul
    resolves = result.nouls["resolves"].noul
    promises_refund = result.nouls["promises_refund"].noul

    problems = []
    if consistent < _THRESHOLD:
        problems.append("Reply is inconsistent with what the customer said.")
    if polite < _THRESHOLD:
        problems.append("Reply is not polite.")
    if resolves < _THRESHOLD:
        problems.append("Reply does not resolve the customer's issue.")
    if promises_refund >= _THRESHOLD:
        problems.append("Reply promises a refund, which only billing may do.")

    refund_ok = 1 - promises_refund
    overall = (consistent + polite + resolves + refund_ok) / 4
    score = max(1, min(10, round(1 + 9 * overall)))

    return {"score": score, "problems": problems}
