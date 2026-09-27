"""Support-ticket triage backed by typesafe.ai's Jev model (System One API)."""

from __future__ import annotations

from dataclasses import dataclass

from typesafe_sdk import Choice, Noul, RetryPolicy, Score, TypeSafeClient, TypeSafeRateLimitError

DEPARTMENTS = {
    "billing": "Charges, invoices, subscriptions, refunds, or payment methods",
    "technical": "Bugs, errors, or integrations not working as expected",
    "account": "Login, password, profile, or account access issues",
    "shipping": "Delivery status, delays, lost/damaged packages, or returns",
    "sales": "Pricing questions, upgrades, or purchasing decisions",
}

SEVERITY_LEVELS = [
    "Cosmetic annoyance or a general question; no impact to using the product",
    "Minor issue with an easy workaround",
    "Major feature broken or degraded; workaround is painful or partial",
    "Critical, blocking issue with no workaround, or affecting many customers or revenue",
]
MOST_SEVERE_LEVEL = len(SEVERITY_LEVELS) - 1

# A second-place department is only reported if it's a plausible alternative,
# not just noise in the probability distribution.
SECONDARY_DEPARTMENT_THRESHOLD = 0.25

# Busy queues hit 429s regularly; retry with backoff before giving up, and cap
# the total time spent retrying so a worker can't stall indefinitely on one ticket.
RATE_LIMIT_RETRY_POLICY = RetryPolicy(
    max_retries=5,
    backoff_initial=0.5,
    backoff_max=20.0,
    backoff_jitter=0.25,
    timeout=60.0,
)


class TriageUnavailableError(RuntimeError):
    """Raised when Jev is rate-limited past the retry budget, so the caller can requeue the ticket."""

    def __init__(self, message: str, retry_after_ms: int | None):
        super().__init__(message)
        self.retry_after_ms = retry_after_ms


@dataclass
class TicketRouting:
    department: str
    secondary_department: str | None
    severity: float
    probability_most_severe: float
    wants_refund: bool
    refund_probability: float


def triage_ticket(text: str, client: TypeSafeClient) -> TicketRouting:
    """Route a support ticket using Jev: department, severity, and refund intent.

    `client` should be a long-lived `TypeSafeClient` shared across calls so the
    queue reuses one connection pool instead of reconnecting per ticket.
    """
    try:
        response = client.system_one(
            state=text,
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
                    instructions="Is the customer asking for a refund or their money back?",
                ),
            },
            retry=RATE_LIMIT_RETRY_POLICY,
        )
    except TypeSafeRateLimitError as exc:
        raise TriageUnavailableError(
            "Jev rate limit exceeded while triaging ticket", exc.retry_after_ms
        ) from exc

    department_answer = response.answers["department"]
    ranked_departments = sorted(
        department_answer.probabilities.items(), key=lambda item: item[1], reverse=True
    )
    secondary_department = None
    if len(ranked_departments) > 1 and ranked_departments[1][1] >= SECONDARY_DEPARTMENT_THRESHOLD:
        secondary_department = ranked_departments[1][0]

    severity_answer = response.answers["severity"]
    probability_most_severe = severity_answer.probabilities.get(
        MOST_SEVERE_LEVEL, severity_answer.probabilities.get(str(MOST_SEVERE_LEVEL), 0.0)
    )

    refund_answer = response.answers["refund"]

    return TicketRouting(
        department=department_answer.choice,
        secondary_department=secondary_department,
        severity=severity_answer.score,
        probability_most_severe=probability_most_severe,
        wants_refund=refund_answer.noul >= 0.5,
        refund_probability=refund_answer.noul,
    )
