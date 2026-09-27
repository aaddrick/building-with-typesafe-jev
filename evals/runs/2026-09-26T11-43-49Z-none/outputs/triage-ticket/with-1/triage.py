"""Support-ticket triage backed by typesafe.ai's Jev model (System One API).

Requires the TYPESAFE_API_KEY environment variable and the `typesafe-sdk`
package (`pip install typesafe-sdk`).
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass

from typesafe_sdk import (
    Choice,
    Noul,
    RetryPolicy,
    Score,
    TypeSafeClient,
    TypeSafeRateLimitError,
)

logger = logging.getLogger(__name__)

_DEPARTMENTS = {
    "billing": "Payment, invoices, subscriptions, or refunds",
    "technical": "Bugs, errors, crashes, or integration/product malfunctions",
    "account": "Login, account access, or profile/settings changes",
    "sales": "Pricing, plans, or upgrade questions",
}

_SEVERITY_LEVELS = [
    "Trivial: cosmetic issue or general question, no impact on the customer's ability to use the product",
    "Minor: limited impact, a workaround exists",
    "Major: a significant feature is broken and there is no workaround",
    "Critical: the product is unusable, data has been lost, or the customer's business is impacted",
]
_MOST_SEVERE_LEVEL = len(_SEVERITY_LEVELS) - 1

_QUESTIONS = {
    "department": Choice(
        instructions="Which department should own this support ticket?",
        criteria=_DEPARTMENTS,
    ),
    "second_department": Choice(
        instructions=(
            "This ticket might plausibly also belong to a second department. "
            "Name that department, or 'none' if only one department applies."
        ),
        criteria={**_DEPARTMENTS, "none": "No other department plausibly applies"},
    ),
    "severity": Score(
        instructions="How severe is the customer's problem?",
        criteria=_SEVERITY_LEVELS,
    ),
    "wants_refund": Noul(
        instructions="Is the customer explicitly asking for a refund?",
    ),
}

# The SDK already retries 429s internally (respecting Retry-After), but on a
# busy queue we want it to try harder than the library default before giving up.
_client = TypeSafeClient(
    retry=RetryPolicy(
        max_retries=5,
        timeout=30.0,
        http_statuses={408, 429, 500, 502, 503, 504},
    )
)


@dataclass
class RoutingDecision:
    department: str
    second_department: str | None
    severity: float
    severity_confidence: float
    probability_most_severe: float
    wants_refund: bool
    refund_probability: float


def triage_ticket(text: str, *, max_rate_limit_retries: int = 3) -> RoutingDecision:
    """Classify a support ticket with Jev and return a routing decision.

    Falls back to its own backoff loop if the SDK's built-in retries are
    exhausted, since a busy queue can keep hitting 429s in bursts.
    """
    attempt = 0
    while True:
        try:
            response = _client.system_one(state=text, questions=_QUESTIONS)
            break
        except TypeSafeRateLimitError as exc:
            attempt += 1
            if attempt > max_rate_limit_retries:
                raise
            delay = exc.retry_after_ms / 1000 if exc.retry_after_ms else min(2**attempt, 30)
            delay += random.uniform(0, delay * 0.1)
            logger.warning(
                "Jev rate limit hit (attempt %d/%d), backing off %.1fs",
                attempt,
                max_rate_limit_retries,
                delay,
            )
            time.sleep(delay)

    department = response.answers["department"].choice
    second_choice = response.answers["second_department"].choice
    second_department = None if second_choice in ("none", department) else second_choice

    severity_answer = response.answers["severity"]
    refund_answer = response.answers["wants_refund"]

    return RoutingDecision(
        department=department,
        second_department=second_department,
        severity=severity_answer.score,
        severity_confidence=severity_answer.confidence,
        probability_most_severe=severity_answer.probabilities.get(_MOST_SEVERE_LEVEL, 0.0),
        wants_refund=refund_answer.noul >= 0.5,
        refund_probability=refund_answer.noul,
    )
