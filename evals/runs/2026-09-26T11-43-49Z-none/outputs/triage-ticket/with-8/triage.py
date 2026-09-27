"""Support-ticket triage using typesafe.ai's Jev model (System One API)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from typesafe_sdk import (
    Choice,
    Noul,
    RetryPolicy,
    Score,
    TypeSafeClient,
    TypeSafeRateLimitError,
)

logger = logging.getLogger(__name__)

DEPARTMENTS = {
    "billing": "Payment, invoicing, subscription, or refund issues.",
    "technical": "Bugs, errors, or integration/product malfunctions.",
    "sales": "Pricing, plan upgrades, or new account questions.",
    "account": "Login, access, or account settings issues.",
}

# Ordered from least to most severe; index 3 is "most severe" for probability reporting below.
SEVERITY_LEVELS = [
    "Minor annoyance with no real impact on using the product.",
    "Noticeable problem, but a workaround exists.",
    "Major problem blocking a core workflow.",
    "Critical/outage-level issue affecting the customer's business.",
]

# A second department is only reported if it's a plausible contender, not just runner-up noise.
SECONDARY_DEPARTMENT_MIN_PROBABILITY = 0.2

_client: TypeSafeClient | None = None


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        # RetryPolicy already retries 429s with backoff, honoring the server's Retry-After header.
        _client = TypeSafeClient(
            retry=RetryPolicy(max_retries=5, backoff_max=20.0, timeout=45.0),
        )
    return _client


@dataclass
class RoutingDecision:
    department: str
    department_confidence: float
    secondary_department: str | None
    severity_label: str
    severity_score: float
    most_severe_probability: float
    refund_requested: bool
    refund_probability: float


def triage_ticket(ticket_text: str) -> RoutingDecision:
    """Classify a support ticket and return a routing decision.

    Raises TypeSafeRateLimitError if the queue is still rate-limited after
    the client's configured retries are exhausted, so callers can requeue.
    """
    client = _get_client()

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
                    instructions="Is the customer explicitly asking for a refund?",
                ),
            },
        )
    except TypeSafeRateLimitError as exc:
        logger.warning(
            "Jev rate limit exceeded after retries; retry after %sms",
            exc.retry_after_ms,
        )
        raise

    department = response.choices["department"]
    severity = response.scores["severity"]
    refund = response.nouls["refund_requested"]

    ranked_departments = sorted(
        department.probabilities.items(), key=lambda item: item[1], reverse=True
    )
    secondary_department = None
    if len(ranked_departments) > 1:
        name, probability = ranked_departments[1]
        if probability >= SECONDARY_DEPARTMENT_MIN_PROBABILITY:
            secondary_department = name

    most_severe_level = max(severity.probabilities)
    nearest_level = min(round(severity.score), most_severe_level)

    return RoutingDecision(
        department=department.choice,
        department_confidence=department.confidence,
        secondary_department=secondary_department,
        severity_label=severity.legend[nearest_level],
        severity_score=severity.score,
        most_severe_probability=severity.probabilities[most_severe_level],
        refund_requested=refund.noul >= 0.5,
        refund_probability=refund.noul,
    )
