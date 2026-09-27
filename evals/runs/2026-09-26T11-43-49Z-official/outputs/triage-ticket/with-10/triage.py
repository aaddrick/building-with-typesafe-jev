"""Support-ticket triage backed by typesafe.ai's Jev (System One) model."""

from __future__ import annotations

import threading
from dataclasses import dataclass

from typesafe_sdk import (
    Choice,
    Noul,
    NoulCriteria,
    RetryPolicy,
    Score,
    TypeSafeClient,
    TypeSafeInternalServerError,
    TypeSafeRateLimitError,
)

DEPARTMENTS = {
    "billing": "Charges, invoices, payments, subscriptions, and refund requests",
    "technical_support": "The product isn't working as expected: bugs, errors, crashes, performance",
    "account": "Login, password, access, account settings, and permissions",
    "shipping": "Order delivery, tracking, shipping delays, or lost/damaged packages",
    "sales": "Questions about purchasing, upgrading, or product fit before buying",
    "general": "Anything that doesn't clearly fit another department",
}

SECONDARY_DEPARTMENT_CRITERIA = {
    **DEPARTMENTS,
    "none": "No second department plausibly applies; the primary department is a clear, exclusive fit",
}

# Ordered from least to most severe; index position is the Score level number.
SEVERITY_LEVELS = ["low", "medium", "high", "critical"]
SEVERITY_CRITERIA = [
    "Cosmetic issue or a general question; no impact on the customer's ability to use the product",
    "A feature is degraded or inconvenient, but a workaround exists and the customer can proceed",
    "A feature is broken with no workaround, blocking the customer's normal use of the product",
    "Complete loss of service, data loss, security exposure, or a widespread outage",
]
MOST_SEVERE_INDEX = len(SEVERITY_LEVELS) - 1

REFUND_THRESHOLD = 0.5

_QUESTIONS = {
    "department": Choice(
        instructions="Which department should handle this support ticket?",
        criteria=DEPARTMENTS,
    ),
    "secondary_department": Choice(
        instructions=(
            "Besides the single best-fitting department, is there a second, different "
            "department that could also plausibly need to be involved in this ticket? "
            "Answer `none` if only one department applies."
        ),
        criteria=SECONDARY_DEPARTMENT_CRITERIA,
    ),
    "severity": Score(
        instructions="How severe is the problem described in this support ticket?",
        criteria=SEVERITY_CRITERIA,
    ),
    "wants_refund": Noul(
        instructions="Is the customer explicitly asking for a refund or their money back?",
        criteria=NoulCriteria(
            true="States or clearly implies they want money back for a charge, order, or subscription",
            false="No request for money back, even if they are unhappy or reporting a problem",
        ),
    ),
}


class TriageError(Exception):
    """Base error for ticket triage failures."""


class TriageTemporarilyUnavailableError(TriageError):
    """Jev is rate limiting or overloaded after the SDK's built-in retries were exhausted.

    Raised on a busy queue instead of letting the raw HTTP error propagate, so the
    caller can requeue the ticket (optionally after `retry_after_seconds`) rather
    than dropping it or crashing the worker.
    """

    def __init__(self, retry_after_seconds: float | None = None):
        self.retry_after_seconds = retry_after_seconds
        suffix = f"; retry after {retry_after_seconds:.1f}s" if retry_after_seconds else ""
        super().__init__(f"Jev is rate limited or overloaded{suffix}")


@dataclass
class TriageResult:
    department: str
    secondary_department: str | None
    severity_level: str
    severity_score: float
    probability_most_severe: float
    severity_confidence: float
    wants_refund: bool
    refund_probability: float


_client: TypeSafeClient | None = None
_client_lock = threading.Lock()


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = TypeSafeClient(
                    retry=RetryPolicy(max_retries=5, backoff_initial=0.5, backoff_max=10.0, timeout=30.0),
                )
    return _client


def close_client() -> None:
    """Close the shared Jev client, e.g. during a graceful worker shutdown."""
    global _client
    with _client_lock:
        if _client is not None:
            _client.close()
            _client = None


def triage_ticket(ticket_text: str) -> TriageResult:
    """Classify a support ticket's department, severity, and refund intent using Jev."""
    client = _get_client()
    try:
        response = client.system_one(
            model="jev-latest",
            state=ticket_text,
            questions=_QUESTIONS,
        )
    except TypeSafeRateLimitError as exc:
        retry_after = exc.retry_after_ms / 1000 if exc.retry_after_ms else None
        raise TriageTemporarilyUnavailableError(retry_after_seconds=retry_after) from exc
    except TypeSafeInternalServerError as exc:
        raise TriageTemporarilyUnavailableError() from exc

    answers = response.answers
    department = answers["department"].choice
    secondary_department = answers["secondary_department"].choice
    if secondary_department in ("none", department):
        secondary_department = None

    severity = answers["severity"]
    predicted_level = max(range(len(SEVERITY_LEVELS)), key=lambda i: severity.probabilities[str(i)])
    refund = answers["wants_refund"]

    return TriageResult(
        department=department,
        secondary_department=secondary_department,
        severity_level=SEVERITY_LEVELS[predicted_level],
        severity_score=severity.score,
        probability_most_severe=severity.probabilities[str(MOST_SEVERE_INDEX)],
        severity_confidence=severity.confidence,
        wants_refund=refund.noul > REFUND_THRESHOLD,
        refund_probability=refund.noul,
    )


if __name__ == "__main__":
    example = (
        "I've been charged twice for my subscription this month and the app still "
        "crashes every time I try to export a report. I want my money back."
    )
    result = triage_ticket(example)
    print(result)
