"""Grade a support agent's reply against a fixed rubric using typesafe.ai's Jev model.

Jev (a System One model) only answers narrow yes/no questions about the given
state -- it does not generate text or make the scoring decision itself. This
module asks Jev four atomic questions and combines the answers into a 1-10
score and a list of problems in code.
"""

from typesafe_sdk import TypeSafeClient, Noul, NoulCriteria

# Pinned because the threshold and weights below were tuned against this
# version's answers; an alias like "jev-latest" could shift them silently.
MODEL = "jev-1.13.0"

# Below this, a Noul answer counts as "no" for the consistency/politeness/
# resolution checks. At or above this, "promises_refund" counts as "yes".
NOUL_THRESHOLD = 0.5

# Weights for the three graded qualities that blend into the score.
# "promises_refund" is not blended in: it is a hard policy violation that
# caps the score instead of averaging into it.
WEIGHT_CONSISTENT = 0.3
WEIGHT_POLITE = 0.2
WEIGHT_RESOLVES = 0.5

# Score cap applied when the reply promises a refund it isn't authorized to promise.
REFUND_VIOLATION_CAP = 3


def grade(customer_message: str, agent_reply: str) -> dict:
    """Grade `agent_reply` against `customer_message` on a 1-10 scale.

    Returns {"score": int, "problems": list[str], "model": str}.
    """
    state = {"customer_message": customer_message, "agent_reply": agent_reply}

    questions = {
        "consistent": Noul(
            instructions=(
                "Is everything `agent_reply` states about the customer's situation "
                "consistent with what `customer_message` actually says, with no "
                "contradictions and no invented facts about the customer's account, "
                "order, or issue?"
            ),
            criteria=NoulCriteria(
                true="Every claim `agent_reply` makes about the customer's situation matches or is supported by `customer_message`",
                false="`agent_reply` contradicts `customer_message`, or states facts about the customer's situation not supported by it",
            ),
        ),
        "polite": Noul(
            instructions="Is the tone of `agent_reply` polite and respectful toward the customer?",
            criteria=NoulCriteria(
                true="Courteous, respectful, professional tone throughout",
                false="Rude, dismissive, condescending, or otherwise disrespectful in any part",
            ),
        ),
        "resolves": Noul(
            instructions=(
                "Does `agent_reply` resolve the issue the customer raised in "
                "`customer_message`, by giving a concrete fix, answer, or clear next "
                "step that addresses that issue, rather than only acknowledging it "
                "or deferring without resolving anything?"
            ),
            criteria=NoulCriteria(
                true="Gives a concrete solution, fix, answer, or actionable next step that addresses the customer's issue",
                false="Only acknowledges the issue, stalls, or fails to address what the customer asked about",
            ),
        ),
        "promises_refund": Noul(
            instructions=(
                "Does `agent_reply` promise, guarantee, or commit to giving the "
                "customer a refund or their money back (for example 'we will refund "
                "you' or 'you'll get your money back'), as opposed to merely "
                "discussing refunds or policy without committing to one?"
            ),
            criteria=NoulCriteria(
                true="Commits to issuing a refund or returning money to the customer",
                false="Does not commit to a refund (may mention refund policy or forward to billing without promising one)",
            ),
        ),
    }

    with TypeSafeClient() as client:
        response = client.system_one(state=state, questions=questions, model=MODEL)

    consistent = response.nouls["consistent"].noul
    polite = response.nouls["polite"].noul
    resolves = response.nouls["resolves"].noul
    promises_refund = response.nouls["promises_refund"].noul

    problems = []
    if consistent < NOUL_THRESHOLD:
        problems.append("Reply is inconsistent with what the customer said.")
    if polite < NOUL_THRESHOLD:
        problems.append("Reply is not polite.")
    if resolves < NOUL_THRESHOLD:
        problems.append("Reply does not resolve the customer's issue.")
    if promises_refund >= NOUL_THRESHOLD:
        problems.append("Reply promises a refund; only Billing may promise refunds.")

    composite = (
        WEIGHT_CONSISTENT * consistent
        + WEIGHT_POLITE * polite
        + WEIGHT_RESOLVES * resolves
    )
    score = 1 + 9 * composite
    if promises_refund >= NOUL_THRESHOLD:
        score = min(score, REFUND_VIOLATION_CAP)
    score = int(round(max(1, min(10, score))))

    return {"score": score, "problems": problems, "model": response.model}
