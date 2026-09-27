"""Grade a support agent's reply with TypeSafe's Jev model.

Jev only answers narrow, typed questions about the state we hand it — it never
writes text and it never sees the refund policy. The policy itself ("only
billing may promise a refund") is a business rule we know in code, so it is
enforced here; Jev is only asked whether the reply *promises a refund at all*.
"""

from __future__ import annotations

from typesafe_sdk import Noul, NoulCriteria, Score, TypeSafeClient

# Pinned so thresholds/weights tuned below keep meaning if the "latest" alias moves.
JEV_MODEL = "jev-1.13.0"

# --- questions -------------------------------------------------------------

QUESTIONS = {
    "consistent": Noul(
        instructions=(
            "Is everything the agent states in `agent_reply` accurate and "
            "consistent with what the customer said in `customer_message`, "
            "with no contradictions or misrepresentations of the customer's "
            "situation?"
        ),
        criteria=NoulCriteria(
            true="The reply's claims about the customer's situation match customer_message",
            false="The reply contradicts or misstates something the customer said",
        ),
    ),
    "resolves": Noul(
        instructions=(
            "Does `agent_reply` fully resolve the issue the customer describes "
            "in `customer_message`, such that the customer would not need to "
            "follow up about this same issue?"
        ),
        criteria=NoulCriteria(
            true="The issue is actually fixed, answered, or a concrete next step is taken",
            false="The reply stalls, deflects, or leaves the issue open",
        ),
    ),
    "politeness": Score(
        instructions="How polite is the agent's tone in `agent_reply` toward the customer?",
        criteria=[
            "Rude, dismissive, or condescending toward the customer",
            "Curt or cold; correct but with no warmth or acknowledgment",
            "Courteous and respectful, addresses the customer properly",
            "Warm, empathetic, and personable while staying professional",
        ],
    ),
    "promises_refund": Noul(
        instructions=(
            "Does `agent_reply` promise, guarantee, or commit to issuing a "
            "refund to the customer, as opposed to merely mentioning a refund "
            "policy or saying the request will be reviewed?"
        ),
        criteria=NoulCriteria(
            true="The agent commits that the customer will get a refund",
            false="No refund commitment is made",
        ),
    ),
}

# --- thresholds and weights (tune these against labeled examples) --------

CONSISTENCY_THRESHOLD = 0.5
RESOLUTION_THRESHOLD = 0.5
POLITENESS_THRESHOLD = 0.5  # normalized score/(len(criteria)-1)
REFUND_THRESHOLD = 0.5

WEIGHTS = {"consistent": 0.3, "resolves": 0.4, "politeness": 0.3}

_client: TypeSafeClient | None = None


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        _client = TypeSafeClient()
    return _client


def grade(customer_message: str, agent_reply: str, *, department: str = "support") -> dict:
    """Grade an agent's reply on a 1-10 scale against the support rubric.

    `department` is the agent's own department, known from routing/ownership
    rather than the text itself. Only "billing" is allowed to promise a refund;
    every other department is flagged for doing so.
    """
    client = _get_client()
    response = client.system_one(
        state={"customer_message": customer_message, "agent_reply": agent_reply},
        questions=QUESTIONS,
        model=JEV_MODEL,
    )

    consistent = response.nouls["consistent"].noul
    resolves = response.nouls["resolves"].noul
    promises_refund = response.nouls["promises_refund"].noul
    politeness = response.scores["politeness"]
    politeness_normalized = politeness.score / (len(QUESTIONS["politeness"].criteria) - 1)

    problems = []

    if consistent < CONSISTENCY_THRESHOLD:
        problems.append("Reply is inconsistent with what the customer said.")

    if resolves < RESOLUTION_THRESHOLD:
        problems.append("Reply does not resolve the customer's issue.")

    if politeness_normalized < POLITENESS_THRESHOLD:
        tone = politeness.legend[round(politeness.score)]
        problems.append(f"Reply is not polite enough (tone: {tone}).")

    if promises_refund >= REFUND_THRESHOLD and department != "billing":
        problems.append(
            "Reply promises a refund, but only the billing department may promise refunds."
        )

    weighted = (
        WEIGHTS["consistent"] * consistent
        + WEIGHTS["resolves"] * resolves
        + WEIGHTS["politeness"] * politeness_normalized
    )
    score = round(1 + 9 * weighted)

    # A refund promised outside billing is a policy violation: cap the score
    # regardless of how well the reply otherwise scores.
    if promises_refund >= REFUND_THRESHOLD and department != "billing":
        score = min(score, 3)

    score = max(1, min(10, score))

    return {"score": score, "problems": problems}
