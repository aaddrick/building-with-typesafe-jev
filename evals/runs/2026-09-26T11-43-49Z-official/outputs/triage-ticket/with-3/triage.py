"""Support-ticket triage using typesafe.ai's Jev model (System One API)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from typesafe_sdk import (
    Choice,
    Noul,
    RetryPolicy,
    Score,
    TypeSafeAPIConnectionError,
    TypeSafeAPITimeoutError,
    TypeSafeClient,
    TypeSafeRateLimitError,
)

# A ticket is considered to plausibly belong to a second department when that
# department's probability is at least this high, even though it wasn't the
# top pick.
SECOND_DEPARTMENT_THRESHOLD = 0.2

# Probability above which we treat a ticket as a refund request.
REFUND_PROBABILITY_THRESHOLD = 0.5

DEPARTMENT_CRITERIA = {
    "billing": "Charges, invoices, payments, and refund requests.",
    "shipping": "Delivery status, delays, lost or misdirected packages.",
    "returns_exchanges": "Wrong, damaged, or unwanted items; exchanges.",
    "technical_support": "Product errors, bugs, or things not working as expected.",
    "account": "Login, password, and account-settings problems.",
    "general_inquiry": "Questions that don't fit another department, e.g. product info.",
}

SEVERITY_CRITERIA = [
    "Cosmetic or minor annoyance; the customer can keep using the product.",
    "Noticeable problem with a workaround; the customer is inconvenienced.",
    "Significant problem with no workaround; a core feature is unusable.",
    "Critical: the customer has lost money, data, or access entirely.",
]

# A queue worker can catch this to requeue the ticket instead of dropping it.
class TriageRateLimitError(Exception):
    """Raised when the Jev API rate limit is hit and retries are exhausted."""

    def __init__(self, retry_after_seconds: Optional[float] = None):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            f"Rate limited by TypeSafe API; retry after {retry_after_seconds}s"
        )


class TriageUnavailableError(Exception):
    """Raised when the Jev API is unreachable or times out after retries."""


@dataclass
class RoutingDecision:
    department: str
    secondary_department: Optional[str]
    severity: str
    severity_score: float
    probability_most_severe: float
    refund_requested: bool
    refund_probability: float


def _make_client() -> TypeSafeClient:
    # Busy queue: retry through transient 429/5xx errors with backoff before
    # giving up, rather than failing the whole batch on the first hiccup.
    return TypeSafeClient(
        retry=RetryPolicy(
            max_retries=5,
            backoff_initial=0.5,
            backoff_max=8.0,
            timeout=30.0,
        )
    )


_default_client: Optional[TypeSafeClient] = None


def _get_default_client() -> TypeSafeClient:
    global _default_client
    if _default_client is None:
        _default_client = _make_client()
    return _default_client


def triage_ticket(
    ticket_text: str, client: Optional[TypeSafeClient] = None
) -> RoutingDecision:
    """Classify a support ticket and return a routing decision.

    Determines the owning department (and a plausible second department, if
    any), how severe the problem is (with the probability it's at the most
    severe level), and whether the customer wants a refund.
    """
    active_client = client or _get_default_client()

    questions = {
        "department": Choice(
            instructions="Which department should handle this support ticket?",
            criteria=DEPARTMENT_CRITERIA,
        ),
        "severity": Score(
            instructions="How severe is the problem described in this ticket?",
            criteria=SEVERITY_CRITERIA,
        ),
        "refund": Noul(
            instructions="Is the customer asking for a refund or their money back?",
            criteria={
                "true": "Explicitly requests a refund, chargeback, or money back.",
                "false": "No request for a refund.",
            },
        ),
    }

    try:
        result = active_client.system_one(ticket_text, questions)
    except TypeSafeRateLimitError as error:
        retry_after = (
            error.retry_after_ms / 1000.0 if error.retry_after_ms else None
        )
        raise TriageRateLimitError(retry_after_seconds=retry_after) from error
    except (TypeSafeAPITimeoutError, TypeSafeAPIConnectionError) as error:
        raise TriageUnavailableError(str(error)) from error

    department_answer = result.choices["department"]
    severity_answer = result.scores["severity"]
    refund_answer = result.nouls["refund"]

    primary_department = department_answer.choice
    secondary_department = None
    runner_up = max(
        (
            (name, probability)
            for name, probability in department_answer.probabilities.items()
            if name != primary_department
        ),
        key=lambda item: item[1],
        default=None,
    )
    if runner_up is not None and runner_up[1] >= SECOND_DEPARTMENT_THRESHOLD:
        secondary_department = runner_up[0]

    most_severe_level = max(severity_answer.probabilities)
    probability_most_severe = severity_answer.probabilities[most_severe_level]
    rounded_level = min(most_severe_level, max(0, round(severity_answer.score)))
    severity_label = severity_answer.legend[rounded_level]

    return RoutingDecision(
        department=primary_department,
        secondary_department=secondary_department,
        severity=severity_label,
        severity_score=severity_answer.score,
        probability_most_severe=probability_most_severe,
        refund_requested=refund_answer.noul >= REFUND_PROBABILITY_THRESHOLD,
        refund_probability=refund_answer.noul,
    )
