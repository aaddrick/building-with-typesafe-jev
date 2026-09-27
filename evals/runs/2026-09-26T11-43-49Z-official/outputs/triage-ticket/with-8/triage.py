"""Support-ticket triage using TypeSafe's Jev model (System One API)."""

from dataclasses import dataclass
from typing import Optional

from typesafe_sdk import Choice, Noul, RetryPolicy, Score, TypeSafeClient

DEPARTMENTS = {
    "billing": "Charges, invoices, payments, subscriptions, and pricing questions.",
    "technical_support": "Bugs, errors, crashes, or a feature not working as expected.",
    "shipping_logistics": "Delivery status, delays, lost or damaged packages, tracking.",
    "account_security": "Login issues, password resets, suspicious activity, access.",
    "sales": "Questions about upgrading, purchasing, or plan comparisons before buying.",
    "general": "Anything that doesn't clearly fit another department.",
}

SEVERITY_LABELS = ["Minor", "Moderate", "Major", "Critical"]
SEVERITY_DESCRIPTIONS = [
    "Cosmetic or informational; no impact on the customer's ability to use the product.",
    "A feature is degraded or annoying, but a workaround exists.",
    "A core feature is broken with no workaround, affecting this customer's use of the product.",
    "The customer is fully blocked, or the ticket describes data loss, a security "
    "exposure, or outage-level impact.",
]
MOST_SEVERE_LEVEL = len(SEVERITY_LABELS) - 1

# A second department is only worth naming when it's a close runner-up to the
# top pick, not whenever it has any nonzero probability at all.
SECONDARY_DEPARTMENT_MARGIN = 0.2

# Tuned for a busy queue: more attempts and a longer overall budget than the
# SDK default, and Retry-After from the server is honored automatically.
_RETRY_POLICY = RetryPolicy(
    max_retries=5,
    timeout=60.0,
    backoff_initial=1.0,
    backoff_max=20.0,
)

_client: Optional[TypeSafeClient] = None


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        _client = TypeSafeClient(retry=_RETRY_POLICY)
    return _client


@dataclass
class RoutingDecision:
    primary_department: str
    department_confidence: float
    secondary_department: Optional[str]
    severity_level: str
    severity_score: float
    most_severe_probability: float
    wants_refund: bool
    refund_probability: float


def triage_ticket(ticket_text: str, *, client: Optional[TypeSafeClient] = None) -> RoutingDecision:
    """Classify a support ticket into a routing decision using Jev.

    Rate limits and transient server errors are retried with exponential
    backoff by the client's RetryPolicy; this raises only once that budget
    is exhausted.
    """
    active_client = client or _get_client()

    response = active_client.system_one(
        state=ticket_text,
        questions={
            "department": Choice(
                instructions=(
                    "Which department should handle this support ticket? Choose "
                    "the department whose responsibility most closely matches "
                    "the customer's primary complaint or request."
                ),
                criteria=DEPARTMENTS,
            ),
            "severity": Score(
                instructions=(
                    "How severe is the problem described in this ticket, from "
                    "the customer's perspective?"
                ),
                criteria=SEVERITY_DESCRIPTIONS,
            ),
            "wants_refund": Noul(
                instructions="Is the customer asking for a refund or their money back?",
                criteria={
                    "true": "Explicitly or clearly asks for a refund, reversal, or credit back.",
                    "false": "No request for money back, even if unhappy or asking for a fix.",
                },
            ),
        },
    )

    department = response.choices["department"]
    severity = response.scores["severity"]
    refund = response.nouls["wants_refund"]

    ranked = sorted(department.probabilities.items(), key=lambda item: item[1], reverse=True)
    secondary_department = None
    if len(ranked) > 1 and ranked[0][1] - ranked[1][1] <= SECONDARY_DEPARTMENT_MARGIN:
        secondary_department = ranked[1][0]

    likely_level = max(severity.probabilities, key=severity.probabilities.get)

    return RoutingDecision(
        primary_department=department.choice,
        department_confidence=department.confidence,
        secondary_department=secondary_department,
        severity_level=SEVERITY_LABELS[likely_level],
        severity_score=severity.score,
        most_severe_probability=severity.probabilities[MOST_SEVERE_LEVEL],
        wants_refund=refund.noul > 0.5,
        refund_probability=refund.noul,
    )
