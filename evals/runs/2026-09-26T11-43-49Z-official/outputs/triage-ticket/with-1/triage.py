"""Support-ticket triage using typesafe.ai's Jev model (System One API).

Classifies an incoming ticket's department, severity, and refund intent in a
single System One call, so it can be dropped into a ticket-processing queue.
"""

from __future__ import annotations

from dataclasses import dataclass

from typesafe_sdk import (
    Choice,
    Noul,
    Score,
    RetryPolicy,
    TypeSafeClient,
    TypeSafeAPIConnectionError,
    TypeSafeAPIError,
    TypeSafeAPITimeoutError,
    TypeSafeRateLimitError,
)

# Departments a ticket can be routed to. Keep descriptions distinct enough
# that adjacent teams (e.g. returns vs. shipping) aren't easily confused.
DEPARTMENTS = {
    "billing": "Charges, invoices, subscriptions, and payment problems",
    "technical_support": "The product is broken, erroring, or not working as documented",
    "shipping_logistics": "Delivery status, delays, lost or misrouted packages",
    "returns_exchanges": "Wrong, damaged, or unwanted items; requests to send an item back",
    "account_access": "Login, password, or account-permission problems",
    "sales": "Questions from a prospective or existing customer about buying more",
    "general_inquiry": "Anything else, including feedback and general questions",
}

# Ordered from least to most severe. `Score` levels are judged independently,
# so each one has to stand on its own rather than relying on relative wording.
SEVERITY_LEVELS = [
    "Cosmetic issue or general question; no impact on the customer's ability to use the product",
    "Inconvenient problem with a workaround; the customer can still get things done",
    "Serious problem blocking a core feature, with no workaround available",
    "Critical emergency: complete outage, data loss, security issue, or safety risk",
]
MOST_SEVERE_LEVEL = len(SEVERITY_LEVELS) - 1

# If the runner-up department's probability is at least this high, the ticket
# is treated as ambiguous and the runner-up is reported as a secondary owner.
SECONDARY_DEPARTMENT_THRESHOLD = 0.25

# A ticket counts as a refund request once the model is fairly confident about it.
REFUND_PROBABILITY_THRESHOLD = 0.6

_client = TypeSafeClient(
    retry=RetryPolicy(
        max_retries=5,
        backoff_initial=0.5,
        backoff_max=8.0,
        timeout=30.0,
        respect_retry_after=True,
        http_statuses={408, 429, 500, 502, 503, 504},
    )
)


class TriageUnavailableError(Exception):
    """Raised when a ticket could not be triaged and should be requeued.

    `retry_after_ms` is populated for rate-limit failures so the caller can
    delay the retry instead of hammering the API again immediately.
    """

    def __init__(self, message: str, *, retry_after_ms: int | None = None):
        super().__init__(message)
        self.retry_after_ms = retry_after_ms


@dataclass
class RoutingDecision:
    department: str
    secondary_department: str | None
    severity_level: str
    severity_score: float
    probability_most_severe: float
    wants_refund: bool
    refund_probability: float


def triage_ticket(ticket_text: str) -> RoutingDecision:
    """Classify a support ticket and return a routing decision.

    Makes one System One call carrying three independent judgments (which
    department owns it, how severe it is, and whether a refund is being
    requested) so they're evaluated in parallel rather than as three
    round trips. Retries on rate limits and transient server errors are
    handled by the client's RetryPolicy; if the queue is still saturated
    after those retries, this raises `TriageUnavailableError` so the caller
    can requeue the ticket instead of losing it.
    """
    try:
        response = _client.system_one(
            ticket_text,
            {
                "department": Choice(
                    instructions="Which department should handle this support ticket?",
                    criteria=DEPARTMENTS,
                ),
                "severity": Score(
                    instructions="How severe is the problem described in this ticket?",
                    criteria=SEVERITY_LEVELS,
                ),
                "wants_refund": Noul(
                    instructions="Is the customer asking for a refund or their money back?",
                ),
            },
            model="jev-latest",
        )
    except TypeSafeRateLimitError as e:
        raise TriageUnavailableError(
            "Rate limited after exhausting retries", retry_after_ms=e.retry_after_ms
        ) from e
    except (TypeSafeAPITimeoutError, TypeSafeAPIConnectionError, TypeSafeAPIError) as e:
        raise TriageUnavailableError(f"Triage request failed: {e}") from e

    department_answer = response.choices["department"]
    probabilities = dict(department_answer.probabilities)
    primary_department = department_answer.choice
    probabilities.pop(primary_department, None)
    secondary_department = None
    if probabilities:
        runner_up, runner_up_probability = max(probabilities.items(), key=lambda kv: kv[1])
        if runner_up_probability >= SECONDARY_DEPARTMENT_THRESHOLD:
            secondary_department = runner_up

    severity_answer = response.scores["severity"]
    most_likely_level = max(severity_answer.probabilities, key=severity_answer.probabilities.get)
    probability_most_severe = severity_answer.probabilities[str(MOST_SEVERE_LEVEL)]

    refund_probability = response.nouls["wants_refund"].noul

    return RoutingDecision(
        department=primary_department,
        secondary_department=secondary_department,
        severity_level=severity_answer.legend[most_likely_level],
        severity_score=severity_answer.score,
        probability_most_severe=probability_most_severe,
        wants_refund=refund_probability >= REFUND_PROBABILITY_THRESHOLD,
        refund_probability=refund_probability,
    )
