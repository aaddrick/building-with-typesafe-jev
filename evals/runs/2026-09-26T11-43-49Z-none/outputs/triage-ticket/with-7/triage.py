"""Support-ticket triage using typesafe.ai's Jev model (System One API)."""

from __future__ import annotations

from dataclasses import dataclass

from typesafe_sdk import (
    Choice,
    Noul,
    RetryPolicy,
    Score,
    TypeSafeClient,
    TypeSafeRateLimitError,
)

DEPARTMENTS = {
    "billing": "Payments, invoices, subscriptions, or refund requests",
    "technical": "Bugs, errors, or product/integration malfunctions",
    "account": "Login, account access, or account-settings issues",
    "sales": "Pricing questions, upgrades, or new purchases",
}

# Ordered from least to most severe; the model scores on this scale (0-indexed).
SEVERITY_LEVELS = [
    "Cosmetic or informational, no impact on the customer's ability to use the product",
    "Minor inconvenience, a workaround exists",
    "Major functionality is broken, no workaround",
    "Critical: the product is unusable or data is at risk",
]
_MOST_SEVERE_LEVEL = len(SEVERITY_LEVELS) - 1

# A ticket only gets a secondary department when the model gives another
# option a real chance of also being correct, not just noise around zero.
_SECONDARY_DEPARTMENT_THRESHOLD = 0.25

_client: TypeSafeClient | None = None


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        _client = TypeSafeClient(
            retry=RetryPolicy(
                max_retries=5,
                backoff_initial=1.0,
                backoff_max=30.0,
                timeout=60.0,
            ),
        )
    return _client


class TicketRateLimited(Exception):
    """Raised when Jev's rate limit is still exceeded after the client's own retries."""

    def __init__(self, retry_after_ms: int | None):
        self.retry_after_ms = retry_after_ms
        super().__init__(f"Jev rate limit exceeded; retry after {retry_after_ms} ms")


@dataclass
class TriageResult:
    department: str
    department_confidence: float
    secondary_department: str | None
    severity_level: int
    severity_label: str
    severity_confidence: float
    most_severe_probability: float
    refund_requested: bool
    refund_probability: float


def triage_ticket(ticket_text: str, *, client: TypeSafeClient | None = None) -> TriageResult:
    """Classify a support ticket into a routing decision using the Jev model.

    Raises `TicketRateLimited` if Jev's rate limit is still exceeded after the
    client's built-in retries, so a queue worker can requeue the ticket instead
    of crashing.
    """
    client = client or _get_client()

    try:
        response = client.system_one(
            state=ticket_text,
            questions={
                "department": Choice(
                    instructions="Which department should handle this support ticket?",
                    criteria=DEPARTMENTS,
                ),
                "severity": Score(
                    instructions="How severe is the customer's problem?",
                    criteria=SEVERITY_LEVELS,
                ),
                "refund_requested": Noul(
                    instructions="Is the customer asking for a refund or their money back?",
                ),
            },
        )
    except TypeSafeRateLimitError as e:
        raise TicketRateLimited(e.retry_after_ms) from e

    department_answer = response.answers["department"]
    severity_answer = response.answers["severity"]
    refund_answer = response.answers["refund_requested"]

    ranked_departments = sorted(
        department_answer.probabilities.items(), key=lambda item: item[1], reverse=True
    )
    secondary_department = None
    if len(ranked_departments) > 1:
        second_label, second_probability = ranked_departments[1]
        if second_probability >= _SECONDARY_DEPARTMENT_THRESHOLD:
            secondary_department = second_label

    return TriageResult(
        department=department_answer.choice,
        department_confidence=department_answer.confidence,
        secondary_department=secondary_department,
        severity_level=severity_answer.score,
        severity_label=SEVERITY_LEVELS[severity_answer.score],
        severity_confidence=severity_answer.confidence,
        most_severe_probability=severity_answer.probabilities[_MOST_SEVERE_LEVEL],
        refund_requested=refund_answer.noul >= 0.5,
        refund_probability=refund_answer.noul,
    )
