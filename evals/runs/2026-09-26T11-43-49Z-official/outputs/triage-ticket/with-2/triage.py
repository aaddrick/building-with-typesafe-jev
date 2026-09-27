"""Support-ticket triage backed by typesafe.ai's Jev model (System One API)."""

from __future__ import annotations

from dataclasses import dataclass

from typesafe_sdk import (
    Choice,
    Noul,
    NoulCriteria,
    RetryPolicy,
    Score,
    TypeSafeClient,
    TypeSafeRateLimitError,
)

DEPARTMENTS = {
    "billing": "Payments, charges, invoices, refunds, and subscription costs",
    "shipping": "Delivery delays, lost or damaged packages, tracking issues",
    "technical": "Product defects, bugs, error messages, app or website malfunctions",
    "account": "Login issues, password resets, profile or settings changes",
    "sales": "Pre-purchase questions, upgrades, plan changes, quotes",
}

SEVERITY_LEVELS = [
    "Cosmetic or minor inconvenience with no real impact on using the product",
    "Functionality is reduced but a workaround exists and the customer can proceed",
    "A core task is blocked with no workaround, but there is no safety, legal, or "
    "financial exposure",
    "Critical: complete outage, data loss, security exposure, or ongoing financial "
    "harm to the customer",
]
_MOST_SEVERE_LEVEL = len(SEVERITY_LEVELS) - 1

_RETRY_POLICY = RetryPolicy(
    max_retries=5,
    backoff_initial=1.0,
    backoff_max=30.0,
    respect_retry_after=True,
    timeout=60.0,
)

_default_client: TypeSafeClient | None = None


def _get_client() -> TypeSafeClient:
    global _default_client
    if _default_client is None:
        _default_client = TypeSafeClient(retry=_RETRY_POLICY)
    return _default_client


class TriageRateLimitedError(RuntimeError):
    """Raised when Jev is still rate-limited after the client's retry budget is spent."""

    def __init__(self, retry_after_ms: int | None) -> None:
        super().__init__(f"Jev rate limit exceeded; retry_after_ms={retry_after_ms}")
        self.retry_after_ms = retry_after_ms


@dataclass(frozen=True)
class RoutingDecision:
    department: str
    secondary_department: str | None
    severity_level: int
    severity_label: str
    probability_most_severe: float
    wants_refund: bool
    refund_probability: float


def _probability_of_level(probabilities: dict, level: int) -> float:
    return probabilities.get(str(level), probabilities.get(level, 0.0))


def triage_ticket(
    ticket_text: str, *, client: TypeSafeClient | None = None
) -> RoutingDecision:
    """Classify a support ticket into a routing decision using Jev.

    Rate limits and transient server errors are retried automatically by the
    SDK's RetryPolicy; TriageRateLimitedError only surfaces once that retry
    budget is exhausted, so callers on a busy queue can catch it and
    re-enqueue the ticket.
    """
    active_client = client or _get_client()

    try:
        result = active_client.system_one(
            {"ticket": ticket_text},
            {
                "department": Choice(
                    instructions=(
                        "Which department should own this support ticket, "
                        "based only on `ticket`?"
                    ),
                    criteria=DEPARTMENTS,
                ),
                "secondary_department": Choice(
                    instructions=(
                        "Besides the primary owning department, is there a second "
                        "department in `ticket` that plausibly also needs to be "
                        "involved? Pick 'none' if only one department applies."
                    ),
                    criteria={**DEPARTMENTS, "none": "No second department applies"},
                ),
                "severity": Score(
                    instructions="How severe is the problem described in `ticket`?",
                    criteria=SEVERITY_LEVELS,
                ),
                "wants_refund": Noul(
                    instructions="Is the customer explicitly asking for a refund in `ticket`?",
                    criteria=NoulCriteria(
                        true="Customer asks for money back, a refund, or a reversed charge",
                        false="No refund is requested, even if money or billing is mentioned",
                    ),
                ),
            },
        )
    except TypeSafeRateLimitError as error:
        raise TriageRateLimitedError(error.retry_after_ms) from error

    department = result.choices["department"].choice
    secondary_department = result.choices["secondary_department"].choice
    if secondary_department in ("none", department):
        secondary_department = None

    severity = result.scores["severity"]
    severity_level = round(severity.score)
    refund = result.nouls["wants_refund"]

    return RoutingDecision(
        department=department,
        secondary_department=secondary_department,
        severity_level=severity_level,
        severity_label=SEVERITY_LEVELS[severity_level],
        probability_most_severe=_probability_of_level(
            severity.probabilities, _MOST_SEVERE_LEVEL
        ),
        wants_refund=refund.noul >= 0.5,
        refund_probability=refund.noul,
    )
