"""Support-ticket triage using typesafe.ai's Jev model (System One API)."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from typesafe_sdk import (
    Choice,
    Noul,
    RetryPolicy,
    Score,
    TypeSafeAPIError,
    TypeSafeClient,
    TypeSafeRateLimitError,
)

logger = logging.getLogger(__name__)

DEPARTMENTS = {
    "billing": "Charges, invoices, payments, subscriptions, refund processing",
    "technical": "Bugs, errors, integration failures, outages, broken features",
    "shipping": "Delivery status, delays, lost or damaged-in-transit packages",
    "returns": "Exchanges, wrong item received, return requests",
    "account": "Login, password, account access, profile or settings changes",
    "sales": "Pricing questions, plan upgrades, new purchases",
}

# Ordered low -> high severity, as required by the Score primitive.
SEVERITY_LEVELS = [
    "Cosmetic issue or general question; no impact on the customer's ability to use the product",
    "Minor issue with a workaround available",
    "Major issue blocking a core feature, no workaround available",
    "Critical issue: outage, data loss, security concern, or the product is unusable",
]

# A second department is only reported if it's a plausible contender, not just noise.
SECONDARY_DEPARTMENT_MIN_PROBABILITY = 0.2

# Applied on top of the client's own RetryPolicy, for sustained rate limiting
# that outlasts the SDK's built-in retry budget (e.g. a busy queue).
MAX_RATE_LIMIT_RETRIES = 5
RATE_LIMIT_FALLBACK_WAIT_SECONDS = 2.0


@dataclass(frozen=True)
class RoutingDecision:
    department: str
    secondary_department: str | None
    severity_level: int
    severity_description: str
    most_severe_probability: float
    refund_requested: bool
    refund_probability: float


def _build_client() -> TypeSafeClient:
    return TypeSafeClient(
        retry=RetryPolicy(max_retries=3, http_statuses={429, 500, 502, 503, 504}),
    )


_default_client: TypeSafeClient | None = None


def _get_default_client() -> TypeSafeClient:
    global _default_client
    if _default_client is None:
        _default_client = _build_client()
    return _default_client


def _call_with_rate_limit_retry(client: TypeSafeClient, state: str, questions: dict):
    attempt = 0
    while True:
        try:
            return client.system_one(state=state, questions=questions)
        except TypeSafeRateLimitError as exc:
            attempt += 1
            if attempt > MAX_RATE_LIMIT_RETRIES:
                logger.error(
                    "Giving up on ticket triage after %d rate-limit retries", attempt - 1
                )
                raise
            wait_seconds = (
                exc.retry_after_ms / 1000
                if exc.retry_after_ms is not None
                else RATE_LIMIT_FALLBACK_WAIT_SECONDS * attempt
            )
            logger.warning(
                "Rate limited by Jev API (attempt %d/%d); waiting %.1fs before retrying",
                attempt,
                MAX_RATE_LIMIT_RETRIES,
                wait_seconds,
            )
            time.sleep(wait_seconds)
        except TypeSafeAPIError as exc:
            logger.error(
                "Jev API error while triaging ticket: %s (request_id=%s)",
                exc,
                exc.request_id,
            )
            raise


def triage_ticket(ticket_text: str, client: TypeSafeClient | None = None) -> RoutingDecision:
    """Classify a support ticket's department, severity, and refund intent.

    Uses Jev's System One API (Choice for department, Score for severity,
    Noul for refund intent) in a single request. Retries on rate limiting
    both at the HTTP-client level and, if that budget is exhausted, with an
    application-level backoff loop suited to a continuously busy queue.
    """
    client = client or _get_default_client()

    questions = {
        "department": Choice(
            instructions="Which department should handle this support ticket?",
            criteria=DEPARTMENTS,
        ),
        "severity": Score(
            instructions="How severe is the customer's problem?",
            criteria=SEVERITY_LEVELS,
        ),
        "refund_requested": Noul(
            instructions="The customer is explicitly asking for a refund or their money back.",
        ),
    }

    response = _call_with_rate_limit_retry(client, ticket_text, questions)

    department = response.choices["department"]
    severity = response.scores["severity"]
    refund = response.nouls["refund_requested"]

    ranked_departments = sorted(
        department.probabilities.items(), key=lambda item: item[1], reverse=True
    )
    secondary_department = None
    if len(ranked_departments) > 1:
        second_name, second_probability = ranked_departments[1]
        if second_probability >= SECONDARY_DEPARTMENT_MIN_PROBABILITY:
            secondary_department = second_name

    most_severe_level = max(severity.legend)
    severity_level = min(max(round(severity.score), 0), most_severe_level)

    return RoutingDecision(
        department=department.choice,
        secondary_department=secondary_department,
        severity_level=severity_level,
        severity_description=severity.legend[severity_level],
        most_severe_probability=severity.probabilities[most_severe_level],
        refund_requested=refund.noul >= 0.5,
        refund_probability=refund.noul,
    )
