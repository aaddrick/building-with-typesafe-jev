"""Support-ticket triage using TypeSafe's Jev model (System One API)."""

from __future__ import annotations

from dataclasses import dataclass

from typesafe_sdk import (
    Choice,
    Noul,
    RetryPolicy,
    Score,
    TypeSafeAPIError,
    TypeSafeClient,
    TypeSafeRateLimitError,
)

MODEL = "jev-1.13.0"

DEPARTMENTS = {
    "billing": "Charges, invoices, payments, subscriptions, or refund requests",
    "technical": "Bugs, errors, a feature not working, performance, or outages",
    "account": "Login, password, profile, or account access/permissions",
    "shipping": "Delivery, tracking, lost or damaged packages, or returns",
    "sales": "Pre-purchase questions, upgrades, pricing, or demos",
    "other": "Does not clearly fit any of the other departments",
}

SEVERITY_LEVELS = [
    "Minor: cosmetic issue or a general question, no impact on using the product",
    "Moderate: a feature is impaired but a workaround exists",
    "Major: a feature is broken with no workaround, blocking a task",
    "Critical: the service is down, data is lost or at risk, a security issue, "
    "or many customers are affected",
]
MOST_SEVERE_LEVEL = len(SEVERITY_LEVELS) - 1

# A second department is only reported when it's a real contender, not just noise.
SECONDARY_DEPARTMENT_THRESHOLD = 0.25

_RETRY_POLICY = RetryPolicy(
    max_retries=6,
    backoff_initial=0.5,
    backoff_max=20.0,
    respect_retry_after=True,
)

_client: TypeSafeClient | None = None


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        _client = TypeSafeClient(model=MODEL, retry=_RETRY_POLICY)
    return _client


class TriageUnavailable(Exception):
    """Jev could not be reached even after the client's built-in retries.

    Callers on a queue should requeue the ticket (respecting retry_after_ms
    when set) instead of dropping it.
    """

    def __init__(self, message: str, *, retry_after_ms: int | None = None):
        super().__init__(message)
        self.retry_after_ms = retry_after_ms


@dataclass
class TriageResult:
    department: str
    department_confidence: float
    secondary_department: str | None
    severity: float
    severity_description: str
    most_severe_probability: float
    refund_requested: float
    model: str


def triage_ticket(ticket_text: str, *, client: TypeSafeClient | None = None) -> TriageResult:
    """Route a support ticket: department (+ a second one if it's a real contender),
    severity (+ how likely the problem is at the most severe level), and whether a
    refund is being requested.
    """
    client = client or _get_client()

    try:
        r = client.system_one(
            state={"ticket": {"text": ticket_text}},
            questions={
                "department": Choice(
                    instructions="Which department should handle `ticket.text`?",
                    criteria=DEPARTMENTS,
                ),
                "severity": Score(
                    instructions="How severe is the problem described in `ticket.text`?",
                    criteria=SEVERITY_LEVELS,
                ),
                "refund": Noul(
                    instructions="Does `ticket.text` ask for a refund or the "
                    "customer's money back?",
                ),
            },
        )
    except TypeSafeRateLimitError as e:
        raise TriageUnavailable(
            f"rate limited after retries: {e}", retry_after_ms=e.retry_after_ms
        ) from e
    except TypeSafeAPIError as e:
        raise TriageUnavailable(f"Jev request failed: {e}") from e

    department = r.choices["department"]
    severity = r.scores["severity"]
    refund = r.nouls["refund"]

    secondary_department = None
    for name, probability in sorted(
        department.probabilities.items(), key=lambda kv: kv[1], reverse=True
    ):
        if name != department.choice and probability >= SECONDARY_DEPARTMENT_THRESHOLD:
            secondary_department = name
            break

    return TriageResult(
        department=department.choice,
        department_confidence=department.confidence,
        secondary_department=secondary_department,
        severity=severity.score,
        severity_description=SEVERITY_LEVELS[MOST_SEVERE_LEVEL],
        most_severe_probability=severity.probabilities[MOST_SEVERE_LEVEL],
        refund_requested=refund.noul,
        model=r.model,
    )
