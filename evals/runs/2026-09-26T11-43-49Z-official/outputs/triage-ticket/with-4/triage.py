"""Support ticket triage using typesafe.ai's Jev model (System One API)."""

from dataclasses import dataclass
from typing import Optional

from typesafe_sdk import (
    AsyncTypeSafeClient,
    Choice,
    Noul,
    RetryPolicy,
    Score,
    TypeSafeAPIConnectionError,
    TypeSafeAPITimeoutError,
    TypeSafeInternalServerError,
    TypeSafeRateLimitError,
)

# Criteria for the department Choice. Keep descriptions mutually exclusive so
# the model isn't forced to guess between overlapping definitions.
DEPARTMENTS = {
    "billing": "Charges, invoices, payments, subscriptions, refunds to a card",
    "shipping": "Delivery status, delays, lost or damaged-in-transit packages",
    "returns": "Exchanging or sending back an item, wrong item received",
    "technical": "The product or service is broken, erroring, or not working as expected",
    "account": "Login, password, account access, or profile/settings changes",
    "general": "Anything else, including general questions and feedback",
}

# Ordered from least to most severe. Score criteria must describe concrete
# situations that stand on their own, not relative degrees.
SEVERITY_LEVELS = [
    "Minor: cosmetic issue or general question, no functional impact",
    "Moderate: a feature is degraded but a workaround exists",
    "Major: a feature or order is broken with no workaround",
    "Critical: complete outage, data loss, or a safety issue, or the customer "
    "cannot use the product/service at all",
]
MOST_SEVERE_LEVEL = len(SEVERITY_LEVELS) - 1

# A runner-up department is only worth surfacing if it's a real contender,
# not just noise in a mostly-confident distribution.
SECOND_DEPARTMENT_MIN_PROBABILITY = 0.25


class TriageUnavailable(Exception):
    """Raised when a ticket can't be triaged after the client's retries are exhausted."""


@dataclass
class RoutingDecision:
    department: str
    department_confidence: float
    secondary_department: Optional[str]
    severity_label: str
    severity_score: float
    probability_most_severe: float
    refund_requested: bool
    refund_probability: float


def build_client() -> AsyncTypeSafeClient:
    """Client tuned for a busy queue: retries rate limits/overload with backoff.

    Reuse one client across tickets rather than constructing a new one per
    call, so connections are pooled and the retry budget below applies per
    ticket rather than being amplified by the caller's own retry loop.
    """
    return AsyncTypeSafeClient(
        retry=RetryPolicy(
            max_retries=6,
            backoff_initial=0.5,
            backoff_max=10.0,
            timeout=45.0,
            http_statuses={408, 429, 500, 502, 503, 504, 529},
        ),
    )


async def triage_ticket(ticket_text: str, client: AsyncTypeSafeClient) -> RoutingDecision:
    """Classify a support ticket into a routing decision using Jev.

    Runs department, severity, and refund judgments in a single System One
    call. Raises TriageUnavailable if the model is unreachable or overloaded
    even after the client's built-in retries are exhausted, so the caller can
    decide whether to requeue the ticket.
    """
    try:
        response = await client.system_one(
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
                    instructions="Is the customer asking for a refund?",
                ),
            },
        )
    except (
        TypeSafeRateLimitError,
        TypeSafeAPITimeoutError,
        TypeSafeAPIConnectionError,
        TypeSafeInternalServerError,
    ) as exc:
        raise TriageUnavailable(f"could not triage ticket: {exc}") from exc

    department = response.choices["department"]
    severity = response.scores["severity"]
    refund = response.nouls["refund_requested"]

    ranked_departments = sorted(
        department.probabilities.items(), key=lambda item: item[1], reverse=True
    )
    secondary_department = None
    if len(ranked_departments) > 1:
        second_name, second_probability = ranked_departments[1]
        if second_probability >= SECOND_DEPARTMENT_MIN_PROBABILITY:
            secondary_department = second_name

    return RoutingDecision(
        department=department.choice,
        department_confidence=department.confidence,
        secondary_department=secondary_department,
        severity_label=severity.legend[round(severity.score)],
        severity_score=severity.score,
        probability_most_severe=severity.probabilities.get(MOST_SEVERE_LEVEL, 0.0),
        refund_requested=refund.noul >= 0.5,
        refund_probability=refund.noul,
    )
