"""Support-ticket triage using TypeSafe's Jev model (System One API).

Classifies a ticket's routing department, severity, and refund intent in a
single request. Independent judgments (department, severity, refund) are
asked together so they run in parallel against the same ticket state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional

from typesafe_sdk import (
    Choice,
    ChoiceAnswer,
    Noul,
    NoulAnswer,
    RetryPolicy,
    Score,
    ScoreAnswer,
    SystemOneResponse,
    TypeSafeClient,
    TypeSafeRateLimitError,
)

DEFAULT_DEPARTMENTS: Mapping[str, str] = {
    "billing": "Charges, invoices, payments, and subscriptions.",
    "technical_support": "Bugs, errors, crashes, or the product not working as expected.",
    "shipping": "Delivery status, tracking, delays, or lost/damaged packages.",
    "account": "Login, password resets, account access, and profile settings.",
    "sales": "Pre-purchase questions, upgrades, pricing, and plan changes.",
}

# Ordered lowest to highest severity; Jev returns a probability-weighted position
# on this scale plus the full distribution, so we can read off the top level's
# probability directly instead of asking a separate question for it.
SEVERITY_LEVELS = [
    "Cosmetic or minor annoyance; does not block use of the product.",
    "Moderate impact; a feature is degraded but a workaround exists.",
    "Major impact; a core feature is broken with no workaround.",
    "Critical; the product is unusable, or there is data loss or a security/financial exposure.",
]

REFUND_CRITERIA = {
    "true": "Explicitly or clearly asks for money back, a refund, or a charge reversal.",
    "false": "No request for money back, even if the customer is unhappy or wants a fix or replacement.",
}

# A second department is only reported when it's a plausible alternative, not
# whenever it has any nonzero probability at all.
SECONDARY_DEPARTMENT_THRESHOLD = 0.2

REFUND_THRESHOLD = 0.5

# Tuned for a busy queue: retries 429s (and other transient errors), honoring
# the server's Retry-After header when present, before giving up.
DEFAULT_RETRY_POLICY = RetryPolicy(
    max_retries=5,
    respect_retry_after=True,
    backoff_initial=0.5,
    backoff_max=8.0,
)


class TicketTriageResponse(SystemOneResponse):
    department: ChoiceAnswer
    severity: ScoreAnswer
    wants_refund: NoulAnswer


@dataclass(frozen=True)
class RoutingDecision:
    department: str
    secondary_department: Optional[str]
    severity: str
    most_severe_probability: float
    wants_refund: bool
    wants_refund_probability: float


class TriageRateLimited(Exception):
    """Jev's rate limit was still exceeded after the client's own retries ran out.

    Callers on a queue should catch this and requeue the ticket (optionally
    after `retry_after_ms`) rather than dropping it.
    """

    def __init__(self, retry_after_ms: Optional[int]):
        self.retry_after_ms = retry_after_ms
        super().__init__(f"Jev rate limit exceeded; retry after {retry_after_ms} ms")


_default_client: Optional[TypeSafeClient] = None


def _get_default_client() -> TypeSafeClient:
    global _default_client
    if _default_client is None:
        _default_client = TypeSafeClient(retry=DEFAULT_RETRY_POLICY)
    return _default_client


def triage_ticket(
    ticket_text: str,
    *,
    client: Optional[TypeSafeClient] = None,
    departments: Mapping[str, str] = DEFAULT_DEPARTMENTS,
) -> RoutingDecision:
    """Decide which department a support ticket should route to.

    `client` should be a long-lived `TypeSafeClient`, reused across calls, so
    its connection pool and retry policy carry over between tickets on the
    queue. If omitted, a shared module-level client is created on first use.

    Raises `TriageRateLimited` if Jev is still rate-limited after the
    client's configured retries are exhausted.
    """
    client = client or _get_default_client()

    try:
        response = client.system_one(
            state={"ticket": ticket_text},
            questions={
                "department": Choice(
                    instructions="Which department should handle this support ticket?",
                    criteria=dict(departments),
                ),
                "severity": Score(
                    instructions="How severe is the customer's problem?",
                    criteria=SEVERITY_LEVELS,
                ),
                "wants_refund": Noul(
                    instructions="Is the customer asking for a refund?",
                    criteria=REFUND_CRITERIA,
                ),
            },
            response_model=TicketTriageResponse,
        )
    except TypeSafeRateLimitError as exc:
        raise TriageRateLimited(exc.retry_after_ms) from exc

    department = response.department
    ranked_departments = sorted(
        department.probabilities.items(), key=lambda item: item[1], reverse=True
    )
    secondary_department = None
    if len(ranked_departments) > 1:
        name, probability = ranked_departments[1]
        if probability >= SECONDARY_DEPARTMENT_THRESHOLD:
            secondary_department = name

    severity = response.severity
    top_level = len(SEVERITY_LEVELS) - 1
    most_severe_probability = severity.probabilities.get(
        top_level, severity.probabilities.get(str(top_level), 0.0)
    )
    severity_index = max(0, min(top_level, round(severity.score)))
    severity_label = severity.legend.get(
        severity_index, severity.legend.get(str(severity_index), SEVERITY_LEVELS[severity_index])
    )

    wants_refund_probability = response.wants_refund.noul

    return RoutingDecision(
        department=department.choice,
        secondary_department=secondary_department,
        severity=severity_label,
        most_severe_probability=most_severe_probability,
        wants_refund=wants_refund_probability >= REFUND_THRESHOLD,
        wants_refund_probability=wants_refund_probability,
    )
