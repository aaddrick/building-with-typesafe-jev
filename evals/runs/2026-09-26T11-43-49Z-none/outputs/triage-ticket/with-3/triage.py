"""Support ticket triage using TypeSafe's Jev model (System One API)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from typesafe_sdk import (
    Choice,
    Noul,
    NoulCriteria,
    RetryPolicy,
    Score,
    TypeSafeAPIConnectionError,
    TypeSafeAPITimeoutError,
    TypeSafeClient,
    TypeSafeRateLimitError,
)

DEPARTMENTS = {
    "billing": "Charges, invoices, payments, subscriptions, refunds",
    "technical_support": "Bugs, errors, outages, product not working as expected",
    "shipping": "Delivery status, delays, lost or damaged-in-transit packages",
    "account": "Login, password, account access, profile settings",
    "sales": "Pre-purchase questions, upgrades, plan changes, quotes",
    "other": "Anything that doesn't clearly fit another department",
}

SEVERITY_LEVELS = [
    "Cosmetic or minor inconvenience; no impact on the customer's ability to use the product",
    "Degraded experience, but a workaround exists",
    "Major functionality is blocked and no workaround exists",
    "Critical: outage, data loss, or a safety/security issue affecting the customer",
]
MOST_SEVERE_LEVEL = len(SEVERITY_LEVELS) - 1

# Minimum probability for a runner-up department to be worth naming as a second owner.
SECONDARY_DEPARTMENT_THRESHOLD = 0.15

# Refund intent below this is treated as "not requesting a refund".
REFUND_THRESHOLD = 0.5


@dataclass(frozen=True)
class TicketRouting:
    department: str
    department_confidence: float
    secondary_department: str | None
    severity_label: str
    severity_score: float
    severity_confidence: float
    most_severe_probability: float
    refund_requested: bool
    refund_probability: float
    request_id: str | None


class TriageUnavailableError(Exception):
    """Raised when the Jev API can't be reached after the SDK's built-in retries are exhausted."""

    def __init__(self, message: str, *, retry_after_seconds: float | None = None) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


@lru_cache(maxsize=1)
def _get_client() -> TypeSafeClient:
    # A busy queue will routinely hit 429s; retry through them with backoff and only
    # surface TriageUnavailableError once the SDK's own retry budget is exhausted.
    return TypeSafeClient(
        model="jev-latest",
        retry=RetryPolicy(
            max_retries=5,
            backoff_initial=0.5,
            backoff_max=10.0,
            timeout=20.0,
        ),
    )


def triage_ticket(text: str) -> TicketRouting:
    """Classify a support ticket into a routing decision.

    Decides the owning department (and a plausible second department, if any),
    how severe the reported problem is, and whether the customer wants a refund.
    Raises TriageUnavailableError if the API is still rate limited or unreachable
    after retries, so the caller can requeue the ticket.
    """
    client = _get_client()

    questions = {
        "department": Choice(
            instructions="Which department should handle this support ticket?",
            criteria=DEPARTMENTS,
        ),
        "severity": Score(
            instructions="How severe is the problem described in this ticket?",
            criteria=SEVERITY_LEVELS,
        ),
        "refund": Noul(
            instructions="Is the customer explicitly asking for a refund or their money back?",
            criteria=NoulCriteria(
                true="Customer asks to be refunded, reimbursed, or given their money back",
                false="No refund request; the customer may still be unhappy or want a fix/replacement",
            ),
        ),
    }

    try:
        response = client.system_one(text, questions)
    except TypeSafeRateLimitError as exc:
        retry_after = exc.retry_after_ms / 1000 if exc.retry_after_ms is not None else None
        raise TriageUnavailableError(
            "Jev API rate limit exceeded after retries; requeue this ticket.",
            retry_after_seconds=retry_after,
        ) from exc
    except (TypeSafeAPITimeoutError, TypeSafeAPIConnectionError) as exc:
        raise TriageUnavailableError(
            "Jev API unreachable after retries; requeue this ticket."
        ) from exc

    department_answer = response.choices["department"]
    severity_answer = response.scores["severity"]
    refund_answer = response.nouls["refund"]

    ranked_departments = sorted(
        department_answer.probabilities.items(), key=lambda item: item[1], reverse=True
    )
    secondary_department = None
    if len(ranked_departments) > 1:
        name, probability = ranked_departments[1]
        if probability >= SECONDARY_DEPARTMENT_THRESHOLD:
            secondary_department = name

    severity_level = max(0, min(MOST_SEVERE_LEVEL, round(severity_answer.score)))

    return TicketRouting(
        department=department_answer.choice,
        department_confidence=department_answer.confidence,
        secondary_department=secondary_department,
        severity_label=severity_answer.legend[severity_level],
        severity_score=severity_answer.score,
        severity_confidence=severity_answer.confidence,
        most_severe_probability=severity_answer.probabilities[MOST_SEVERE_LEVEL],
        # Jev 1.13 is known to be inconsistent on refund/financial Nouls, so expose the
        # raw probability alongside the thresholded bool for callers that want a second check.
        refund_requested=refund_answer.noul >= REFUND_THRESHOLD,
        refund_probability=refund_answer.noul,
        request_id=response.request_id,
    )
