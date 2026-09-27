"""Support ticket triage using typesafe.ai's Jev model (System One API).

See https://docs.typesafe.ai for the underlying `system_one` primitives
(Choice, Score, Noul) this module builds on.
"""

from dataclasses import dataclass
from typing import Optional

from typesafe_sdk import (
    Choice,
    Noul,
    RetryPolicy,
    Score,
    TypeSafeClient,
)

DEPARTMENTS = {
    "billing": "Charges, invoices, payments, subscriptions, or pricing disputes",
    "technical": "Bugs, errors, integration failures, or product malfunctions",
    "account": "Login, access, profile, or account settings issues",
    "sales": "Pre-purchase questions, upgrades, or new account inquiries",
}

# Ordered low -> high; index doubles as the Score primitive's level number.
SEVERITY_LEVELS = [
    "Minor annoyance or cosmetic issue with no functional impact",
    "Feature degraded or broken, but a workaround exists",
    "Critical failure blocking the customer with no workaround",
]
MOST_SEVERE_LEVEL = str(len(SEVERITY_LEVELS) - 1)

# Below this, the top department pick isn't a strong enough signal to ignore
# the runner-up, so we surface it as a second candidate for a human to check.
LOW_CONFIDENCE_THRESHOLD = 0.5

# Bounded retry budget so one rate-limited ticket can't stall the whole queue;
# the SDK already backs off exponentially and honors Retry-After headers.
_client = TypeSafeClient(
    model="jev",
    retry=RetryPolicy(
        max_retries=5,
        timeout=30.0,
        http_statuses={429, 500, 502, 503, 504},
        respect_retry_after=True,
    ),
)


@dataclass
class RoutingDecision:
    department: str
    secondary_department: Optional[str]
    severity_level: str
    severity_score: float
    most_severe_probability: float
    refund_requested: bool
    refund_probability: float


def triage_ticket(ticket_text: str) -> RoutingDecision:
    """Classify a support ticket and return a routing decision.

    Raises whatever typesafe_sdk.TypeSafeAPIError subclass the SDK raises once
    its own retry budget (see `_client`'s RetryPolicy) is exhausted, e.g.
    TypeSafeRateLimitError -- callers on a queue should catch that and requeue
    the ticket rather than drop it.
    """
    response = _client.system_one(
        state=ticket_text,
        questions={
            "department": Choice(
                instructions="Which department should handle this support ticket?",
                criteria=DEPARTMENTS,
            ),
            "severity": Score(
                instructions="How severe is the problem described in this ticket?",
                criteria=SEVERITY_LEVELS,
            ),
            "refund_requested": Noul(
                instructions="Is the customer asking for a refund?",
                criteria={
                    "true": "Explicitly or implicitly requests money back, a refund, or a reversed charge",
                    "false": "No request for a refund is made",
                },
            ),
        },
    )

    department_answer = response.answers["department"]
    severity_answer = response.answers["severity"]
    refund_answer = response.answers["refund_requested"]

    secondary_department = None
    if department_answer.confidence < LOW_CONFIDENCE_THRESHOLD:
        runner_up, _ = sorted(
            department_answer.probabilities.items(), key=lambda kv: kv[1], reverse=True
        )[1]
        secondary_department = runner_up

    severity_index = round(severity_answer.score)
    severity_index = max(0, min(len(SEVERITY_LEVELS) - 1, severity_index))

    return RoutingDecision(
        department=department_answer.choice,
        secondary_department=secondary_department,
        severity_level=SEVERITY_LEVELS[severity_index],
        severity_score=severity_answer.score,
        most_severe_probability=severity_answer.probabilities.get(MOST_SEVERE_LEVEL, 0.0),
        refund_requested=refund_answer.noul >= 0.5,
        refund_probability=refund_answer.noul,
    )
