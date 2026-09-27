"""Support-ticket triage using TypeSafe AI's Jev model (System One API)."""

from __future__ import annotations

from dataclasses import dataclass

from typesafe_sdk import Choice, Noul, RetryPolicy, Score, TypeSafeClient

MODEL = "jev-1.13.0"

DEPARTMENTS = {
    "billing": "Charges, invoices, payments, refunds, subscription cost.",
    "technical": "Bugs, errors, outages, broken features, how something works.",
    "account": "Login, password, account access, account settings, security.",
    "shipping": "Order delivery, tracking, damaged or missing packages.",
    "sales": "Upgrading, purchasing, or pricing questions before buying.",
    "other": "None of the above.",
}

# Each level is one situation on a single dimension, judged on its own.
SEVERITY_LEVELS = [
    "Cosmetic issue or question; no impact on using the product.",
    "Minor problem with a workaround; product is still usable.",
    "Major problem blocking a core feature; no workaround exists.",
    "Complete outage or data loss affecting the customer's business.",
]
MOST_SEVERE_LEVEL = len(SEVERITY_LEVELS) - 1

# A second department is only reported when its probability clears this bar.
SECOND_DEPARTMENT_THRESHOLD = 0.25

# The SDK retries 429/5xx on its own; this just widens the budget for a busy
# queue where a burst of tickets can collide with the shared rate limit.
_RETRY_POLICY = RetryPolicy(
    max_retries=5,
    backoff_initial=0.5,
    backoff_max=20.0,
    respect_retry_after=True,
)

# One client, reused across calls and threads, per the SDK's lifecycle guidance.
_client = TypeSafeClient(retry=_RETRY_POLICY)


@dataclass
class RoutingDecision:
    department: str
    department_confidence: float
    second_department: str | None
    severity_level: int
    severity_description: str
    severity_confidence: float
    most_severe_probability: float
    refund_requested: float
    model: str


def triage_ticket(ticket_text: str, *, client: TypeSafeClient | None = None) -> RoutingDecision:
    """Classify a support ticket and return a routing decision.

    Runs one System One request with every question the router needs, so it
    costs a single round trip. Raises a TypeSafeError subclass (see the
    typesafe_sdk exception hierarchy) if the call still fails after the
    client's retry policy is exhausted; callers on a queue should let that
    propagate so the ticket can be requeued rather than silently dropped.
    """
    client = client or _client

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
                instructions="Does `ticket_text` ask for a refund or money back?",
            ),
        },
        model=MODEL,
    )

    department = response.choices["department"]
    severity = response.scores["severity"]
    refund = response.nouls["refund"]

    other_probs = {
        name: prob for name, prob in department.probabilities.items() if name != department.choice
    }
    second_department = None
    if other_probs:
        name, prob = max(other_probs.items(), key=lambda kv: kv[1])
        if prob > SECOND_DEPARTMENT_THRESHOLD:
            second_department = name

    severity_level = min(round(severity.score), MOST_SEVERE_LEVEL)

    return RoutingDecision(
        department=department.choice,
        department_confidence=department.confidence,
        second_department=second_department,
        severity_level=severity_level,
        severity_description=severity.legend[severity_level],
        severity_confidence=severity.confidence,
        most_severe_probability=severity.probabilities.get(MOST_SEVERE_LEVEL, 0.0),
        refund_requested=refund.noul,
        model=response.model,
    )
