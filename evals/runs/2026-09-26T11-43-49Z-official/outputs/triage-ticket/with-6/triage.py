from __future__ import annotations

import logging
import threading
from dataclasses import dataclass

from typesafe_sdk import (
    Choice,
    Noul,
    RetryPolicy,
    Score,
    TypeSafeAPIError,
    TypeSafeClient,
)

logger = logging.getLogger(__name__)

DEFAULT_DEPARTMENTS: dict[str, str] = {
    "billing": "Payments, invoices, charges, subscriptions, refunds, and pricing questions",
    "technical": "Product defects, errors, bugs, or performance and integration problems",
    "account": "Login, security, profile changes, and account-access issues",
    "shipping": "Delivery status, delays, lost or damaged packages",
    "general": "Anything that does not clearly fit one of the other departments",
}

SEVERITY_LEVELS: list[str] = [
    "Minor annoyance or question; no impact on using the product or service",
    "Noticeable problem with a workaround available",
    "Significant problem blocking normal use of the product, with no workaround",
    "Critical issue: complete outage, data loss, safety risk, or major business impact",
]

# A department is only worth naming as a second candidate once it holds a real
# share of the probability mass, not just whatever is left over after the winner.
SECONDARY_DEPARTMENT_THRESHOLD = 0.25

# Tuned for a busy queue: retry through rate limits and transient 5xx/connection
# errors with backoff, but give up within a bounded budget so a stuck ticket
# can't stall the whole worker.
QUEUE_RETRY_POLICY = RetryPolicy(
    max_retries=5,
    backoff_initial=0.5,
    backoff_max=8.0,
    backoff_jitter=0.25,
    respect_retry_after=True,
    timeout=45.0,
)

_client_lock = threading.Lock()
_shared_client: TypeSafeClient | None = None


def _get_shared_client() -> TypeSafeClient:
    """Lazily create one pooled client, shared across triage calls on the queue."""
    global _shared_client
    if _shared_client is None:
        with _client_lock:
            if _shared_client is None:
                _shared_client = TypeSafeClient(retry=QUEUE_RETRY_POLICY)
    return _shared_client


class TriageUnavailableError(RuntimeError):
    """Raised when Jev can't be reached after the configured retries."""


@dataclass(frozen=True)
class TicketTriage:
    department: str
    department_confidence: float
    secondary_department: str | None
    severity_level: str
    severity_index: int
    severity_score: float
    probability_most_severe: float
    refund_requested: bool
    refund_probability: float


def triage_ticket(
    ticket_text: str,
    *,
    client: TypeSafeClient | None = None,
    departments: dict[str, str] | None = None,
    severity_levels: list[str] | None = None,
) -> TicketTriage:
    """Classify a support ticket with Jev and return a routing decision.

    Reuses a shared, retrying client by default so callers processing a queue
    of tickets don't pay connection setup cost per ticket and transparently
    ride out rate limits (429) and transient server errors.
    """
    departments = departments or DEFAULT_DEPARTMENTS
    severity_levels = severity_levels or SEVERITY_LEVELS
    active_client = client or _get_shared_client()

    questions = {
        "department": Choice(
            instructions="Which department should handle this support ticket?",
            criteria=departments,
        ),
        "severity": Score(
            instructions="How severe is the customer's problem?",
            criteria=severity_levels,
        ),
        "refund_requested": Noul(
            instructions="Is the customer asking for a refund or their money back?",
        ),
    }

    try:
        response = active_client.system_one(state=ticket_text, questions=questions)
    except TypeSafeAPIError as exc:
        logger.warning("Jev triage request failed after retries: %s", exc)
        raise TriageUnavailableError(f"could not triage ticket: {exc}") from exc

    department_answer = response.choices["department"]
    severity_answer = response.scores["severity"]
    refund_answer = response.nouls["refund_requested"]

    ranked_departments = sorted(
        department_answer.probabilities.items(), key=lambda item: item[1], reverse=True
    )
    secondary_department = None
    if len(ranked_departments) > 1:
        second_name, second_probability = ranked_departments[1]
        if second_probability >= SECONDARY_DEPARTMENT_THRESHOLD:
            secondary_department = second_name

    predicted_level = max(severity_answer.probabilities, key=severity_answer.probabilities.get)
    top_level = len(severity_levels) - 1
    probability_most_severe = severity_answer.probabilities.get(top_level, 0.0)

    return TicketTriage(
        department=department_answer.choice,
        department_confidence=department_answer.confidence,
        secondary_department=secondary_department,
        severity_level=severity_answer.legend[predicted_level],
        severity_index=predicted_level,
        severity_score=severity_answer.score,
        probability_most_severe=probability_most_severe,
        refund_requested=refund_answer.noul >= 0.5,
        refund_probability=refund_answer.noul,
    )
