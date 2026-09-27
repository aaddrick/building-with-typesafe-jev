"""Support-ticket triage using typesafe.ai's Jev model (System One API).

Docs: https://docs.typesafe.ai
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache

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
    "billing": "Charges, invoices, refunds, or payment problems",
    "shipping": "Delivery status, delays, or lost/missing packages",
    "returns": "Exchanges, or wrong/damaged items",
    "technical": "A product defect, bug, or feature not working",
    "account": "Login, password, or account access issues",
}

SEVERITY_LEVELS = [
    "Cosmetic or informational; no real impact on the customer",
    "Minor inconvenience; a workaround exists",
    "Significant problem; no workaround, but the product/service is still usable",
    "Severe; the customer is fully blocked or facing major loss",
]
MOST_SEVERE_LEVEL = len(SEVERITY_LEVELS) - 1

# Below this, the top department pick isn't concentrated enough to trust on
# its own, so we surface the runner-up as a possible second department.
DEPARTMENT_CONFIDENCE_FLOOR = 0.6

_RETRY_POLICY = RetryPolicy(
    max_retries=5,
    backoff_initial=1.0,
    backoff_max=20.0,
    timeout=60.0,
    # Defaults already retry 408/429/5xx and honor Retry-After; kept explicit
    # here since rate limits are the primary failure mode on a busy queue.
    http_statuses={408, 429, 500, 502, 503, 504},
    respect_retry_after=True,
)


@lru_cache(maxsize=1)
def _get_client() -> TypeSafeClient:
    return TypeSafeClient(retry=_RETRY_POLICY)


@dataclass
class TriageResult:
    department: str
    secondary_department: str | None
    severity: float
    severity_confidence: float
    most_severe_probability: float
    wants_refund: bool
    refund_probability: float


def triage_ticket(ticket_text: str, *, client: TypeSafeClient | None = None) -> TriageResult:
    """Classify a support ticket into a department, severity, and refund intent.

    Raises TypeSafeRateLimitError if the client's retry budget is exhausted
    while the queue is under sustained rate limiting; callers on a queue
    should treat that as a signal to requeue the ticket rather than drop it.
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
                "refund": Noul(
                    instructions="Is the customer explicitly asking for a refund?",
                ),
            },
        )
    except TypeSafeRateLimitError as exc:
        logger.warning(
            "Jev rate limit exhausted after retries (retry_after_ms=%s)",
            exc.retry_after_ms,
        )
        raise

    department = response.choices["department"]
    severity = response.scores["severity"]
    refund = response.nouls["refund"]

    return TriageResult(
        department=department.choice,
        secondary_department=_secondary_department(department),
        severity=severity.score,
        severity_confidence=severity.confidence,
        most_severe_probability=severity.probabilities.get(MOST_SEVERE_LEVEL, 0.0),
        wants_refund=refund.noul >= 0.5,
        refund_probability=refund.noul,
    )


def _secondary_department(answer) -> str | None:
    if answer.confidence >= DEPARTMENT_CONFIDENCE_FLOOR:
        return None
    runner_up = sorted(
        answer.probabilities.items(), key=lambda item: item[1], reverse=True
    )[1:2]
    return runner_up[0][0] if runner_up else None
