"""Support ticket triage backed by typesafe.ai's Jev model (System One API)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from typesafe_sdk import (
    Choice,
    Noul,
    RetryPolicy,
    Score,
    TypeSafeClient,
    TypeSafeRateLimitError,
)

DEPARTMENTS = {
    "technical": "Bugs, errors, crashes, or the product not working as expected",
    "billing": "Charges, invoices, subscriptions, or payment methods",
    "shipping": "Delivery status, delays, lost or damaged packages",
    "account": "Login, password, profile, or account access issues",
    "sales": "Pricing, plans, upgrades, or pre-purchase questions",
    "general": "Anything that doesn't clearly fit another department",
}

# Ordered low to high; Score evaluates each level independently of its position,
# so each one describes a concrete situation rather than just a severity label.
SEVERITY_LEVELS = [
    "Minor annoyance or question with no functional impact",
    "A feature is degraded or inconvenient to use, but a workaround exists",
    "A feature is broken with no workaround, blocking the customer's use of the product",
    "Critical: business-impacting outage, data loss, security issue, or safety risk",
]

# A second-place department below this probability is treated as noise rather
# than a genuine secondary match worth surfacing to a human.
SECOND_DEPARTMENT_THRESHOLD = 0.2

_client: Optional[TypeSafeClient] = None


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        # This runs on a busy queue and can burst past typesafe.ai's per-minute
        # limit, so retry 429s aggressively and honor any Retry-After header.
        _client = TypeSafeClient(
            retry=RetryPolicy(
                max_retries=6,
                backoff_initial=1.0,
                backoff_max=30.0,
                respect_retry_after=True,
                timeout=60.0,
            )
        )
    return _client


class TriageRateLimitedError(RuntimeError):
    """Raised when Jev is still rate-limited after the client's own retries are exhausted."""

    def __init__(self, retry_after_ms: Optional[int]):
        self.retry_after_ms = retry_after_ms
        message = "Jev API rate limit exceeded"
        if retry_after_ms is not None:
            message += f"; retry after {retry_after_ms} ms"
        super().__init__(message)


@dataclass
class TriageResult:
    department: str
    department_confidence: float
    secondary_department: Optional[str]
    severity_level: str
    severity_score: float
    severity_confidence: float
    most_severe_probability: float
    refund_requested: bool
    refund_probability: float


def triage_ticket(ticket_text: str, *, client: Optional[TypeSafeClient] = None) -> TriageResult:
    """Classify a support ticket's department, severity, and refund intent via Jev."""
    active_client = client or _get_client()

    try:
        response = active_client.system_one(
            state=ticket_text,
            questions={
                "department": Choice(
                    instructions="Which department should handle this support ticket?",
                    criteria=DEPARTMENTS,
                ),
                "severity": Score(
                    instructions="How severe is the problem described in this ticket?",
                    criteria=SEVERITY_LEVELS,
                ),
                "refund": Noul(
                    instructions="Is the customer asking for a refund?",
                ),
            },
        )
    except TypeSafeRateLimitError as exc:
        raise TriageRateLimitedError(exc.retry_after_ms) from exc

    department_answer = response.answers["department"]
    severity_answer = response.answers["severity"]
    refund_answer = response.answers["refund"]

    ranked_departments = sorted(
        department_answer.probabilities.items(), key=lambda item: item[1], reverse=True
    )
    secondary_department = None
    if len(ranked_departments) > 1 and ranked_departments[1][1] >= SECOND_DEPARTMENT_THRESHOLD:
        secondary_department = ranked_departments[1][0]

    top_level = len(SEVERITY_LEVELS) - 1
    most_severe_probability = severity_answer.probabilities.get(
        top_level, severity_answer.probabilities.get(str(top_level), 0.0)
    )
    severity_index = max(0, min(top_level, round(severity_answer.score)))

    return TriageResult(
        department=department_answer.choice,
        department_confidence=department_answer.confidence,
        secondary_department=secondary_department,
        severity_level=SEVERITY_LEVELS[severity_index],
        severity_score=severity_answer.score,
        severity_confidence=severity_answer.confidence,
        most_severe_probability=most_severe_probability,
        refund_requested=refund_answer.noul >= 0.5,
        refund_probability=refund_answer.noul,
    )
