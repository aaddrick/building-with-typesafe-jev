"""Grade a support agent's reply using typesafe.ai's Jev model.

Requires `TYPESAFE_API_KEY` to be set in the environment.
"""

from typesafe_sdk import Noul, TypeSafeClient

MODEL = "jev-latest"

# Below this probability a Noul judgment is treated as "no" for the rubric.
DECISION_THRESHOLD = 0.5

# A refund promise is a hard policy violation, not something other strengths
# can offset, so it caps the score instead of being averaged in.
REFUND_VIOLATION_SCORE_CAP = 3.0


def grade(customer_message: str, agent_reply: str) -> dict:
    state = {
        "customer_message": customer_message,
        "agent_reply": agent_reply,
    }

    questions = {
        "consistent": Noul(
            instructions=(
                "Does `agent_reply` accurately reflect what the customer said in "
                "`customer_message`, without contradicting, misquoting, or "
                "mischaracterizing it?"
            ),
            criteria={
                "true": "The reply's claims about the situation match what the customer described.",
                "false": "The reply contradicts, ignores, or misstates something the customer said.",
            },
        ),
        "polite": Noul(
            instructions="Is `agent_reply` polite and respectful in tone toward the customer?",
            criteria={
                "true": "The tone is courteous and respectful throughout.",
                "false": "The tone is rude, dismissive, curt, or condescending anywhere in the reply.",
            },
        ),
        "resolves_issue": Noul(
            instructions=(
                "Does `agent_reply` actually resolve the customer's issue described in "
                "`customer_message`, or give a concrete next step that resolves it "
                "(not just acknowledge or apologize for it)?"
            ),
            criteria={
                "true": "The customer's problem is fixed, or a concrete resolving action/next step is given.",
                "false": "The reply only acknowledges, apologizes, or deflects without resolving anything.",
            },
        ),
        "promises_refund": Noul(
            instructions=(
                "Does `agent_reply` promise, offer, or commit to a refund for the "
                "customer? Only the Billing team is authorized to promise refunds, "
                "so any refund commitment from this agent is against policy."
            ),
            criteria={
                "true": "The reply promises, offers, or commits to a refund.",
                "false": "The reply makes no refund promise (it may still refer the customer to Billing).",
            },
        ),
    }

    with TypeSafeClient() as client:
        response = client.system_one(state=state, questions=questions, model=MODEL)

    consistent = response.nouls["consistent"].noul
    polite = response.nouls["polite"].noul
    resolves_issue = response.nouls["resolves_issue"].noul
    promises_refund = response.nouls["promises_refund"].noul

    problems = []
    if consistent < DECISION_THRESHOLD:
        problems.append("Reply is inconsistent with what the customer said.")
    if polite < DECISION_THRESHOLD:
        problems.append("Reply is not polite.")
    if resolves_issue < DECISION_THRESHOLD:
        problems.append("Reply does not resolve the customer's issue.")
    if promises_refund >= DECISION_THRESHOLD:
        problems.append("Reply promises a refund, which only Billing may do.")

    weighted_avg = (consistent + polite + resolves_issue) / 3
    score = 1 + 9 * weighted_avg
    if promises_refund >= DECISION_THRESHOLD:
        score = min(score, REFUND_VIOLATION_SCORE_CAP)

    return {
        "score": round(score, 1),
        "problems": problems,
    }
