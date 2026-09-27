"""Support ticket triage using TypeSafe's Jev model (System One API).

One `system_one` call per ticket asks all three questions in parallel
(speculative fan-out), then code combines the typed answers into a
routing decision. Pin the model version since thresholds below are
tuned against it.
"""

from __future__ import annotations

from dataclasses import dataclass

from typesafe_sdk import Choice, Noul, RetryPolicy, Score, TypeSafeClient

MODEL = "jev-1.13.0"

# Reviewed and tuned by humans; keep thresholds and criteria together.
DEPARTMENTS = {
    "billing": "Charges, payments, invoices, subscriptions, refunds.",
    "technical": "The product is broken, erroring, or behaving unexpectedly.",
    "account": "Login, access, password, permissions, profile settings.",
    "sales": "Upgrading, pricing questions, new purchases, plan changes.",
    "other": "Doesn't clearly fit billing, technical, account, or sales.",
}

# Concrete situations, one dimension (blockage), not vague degree words.
SEVERITY_LEVELS = [
    "Cosmetic issue or general question; no impact on using the product.",
    "Minor problem with a workaround; the customer can still get their task done.",
    "Major feature is broken with no workaround; the customer is blocked on that feature.",
    "Complete outage, data loss, or security issue; the customer cannot use the "
    "product at all, or their account or data is at risk.",
]
MOST_SEVERE_LEVEL = len(SEVERITY_LEVELS) - 1

# A second department is only reported when it is plausible, not merely
# non-zero. See building-with-typesafe-jev SKILL.md, "Belongs to two categories?".
SECOND_DEPARTMENT_THRESHOLD = 0.25

# Tuned for a busy queue: a shared account-wide rate limit means many workers
# can hit 429 at once, so retry with backoff rather than failing the ticket.
QUEUE_RETRY_POLICY = RetryPolicy(
    max_retries=6,
    backoff_initial=1.0,
    backoff_max=30.0,
    backoff_jitter=0.25,
    respect_retry_after=True,
)

# One client for the whole process (per api-reference.md: do not create a
# client per request); safe to share across worker threads.
_client: TypeSafeClient | None = None


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        _client = TypeSafeClient(retry=QUEUE_RETRY_POLICY, timeout=15.0)
    return _client


@dataclass
class RoutingDecision:
    department: str
    department_confidence: float
    second_department: str | None  # only set above SECOND_DEPARTMENT_THRESHOLD
    severity_level: int  # index into SEVERITY_LEVELS
    severity_label: str
    severity_confidence: float
    most_severe_probability: float  # P(severity_level == MOST_SEVERE_LEVEL)
    wants_refund: bool
    refund_probability: float
    model: str


def triage_ticket(
    ticket_text: str, *, client: TypeSafeClient | None = None
) -> RoutingDecision:
    """Classify a support ticket into a routing decision via one Jev call.

    Raises whatever the SDK raises once its own 429/5xx retries (see
    QUEUE_RETRY_POLICY) are exhausted; callers on a queue should requeue
    the ticket rather than drop it.
    """
    client = client or _get_client()

    response = client.system_one(
        state={"ticket_text": ticket_text},
        questions={
            "department": Choice(
                instructions="Which department should handle `ticket_text`?",
                criteria=DEPARTMENTS,
            ),
            "severity": Score(
                instructions="How severe is the problem described in `ticket_text`?",
                criteria=SEVERITY_LEVELS,
            ),
            "refund": Noul(
                instructions="Is the customer asking for a refund in `ticket_text`?",
            ),
        },
        model=MODEL,
    )

    department = response.choices["department"]
    severity = response.scores["severity"]
    refund = response.nouls["refund"]

    second_department = None
    for name, probability in department.probabilities.items():
        if name != department.choice and probability >= SECOND_DEPARTMENT_THRESHOLD:
            second_department = name
            break

    # Route on the nearest level, clipped to the valid range (patterns.md).
    severity_level = min(int(severity.score + 0.5), MOST_SEVERE_LEVEL)

    return RoutingDecision(
        department=department.choice,
        department_confidence=department.confidence,
        second_department=second_department,
        severity_level=severity_level,
        severity_label=SEVERITY_LEVELS[severity_level],
        severity_confidence=severity.confidence,
        most_severe_probability=severity.probabilities[MOST_SEVERE_LEVEL],
        wants_refund=refund.noul >= 0.5,
        refund_probability=refund.noul,
        model=response.model,
    )
