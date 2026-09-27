"""Support ticket triage using TypeSafe's Jev model (System One API).

One System One request per ticket answers every question triage needs
(department, severity, refund intent) in parallel; the routing policy
itself — thresholds for a secondary department and for "wants a refund"
— lives in code so it can be tuned without another API call.
"""

from __future__ import annotations

import logging
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

# Pin the version the thresholds below were tuned against.
MODEL = "jev-1.13.0"

DEPARTMENTS = {
    "billing": "Charges, invoices, payments, subscriptions, pricing, refunds.",
    "technical": "The product is broken, erroring, or not behaving as documented.",
    "account": "Login, password, access, permissions, or profile data.",
    "shipping": "Order fulfillment, delivery, tracking, missing or damaged packages.",
    "sales": "Pre-purchase questions, upgrades, plan changes, demos.",
    "other": "Doesn't fit any department above.",
}

# Each level is judged on its own, so it describes a situation, not a
# point on a "worse than the last one" scale.
SEVERITY_LEVELS = [
    "Cosmetic issue or general question; no impact on using the product.",
    "Functional problem with a workaround; the customer can still get by.",
    "Major feature is broken with no workaround, blocking normal use.",
    "Complete outage, data loss, security exposure, or direct financial harm.",
]
MOST_SEVERE_LEVEL = len(SEVERITY_LEVELS) - 1

# A second department is only worth surfacing when it's a real
# contender, not noise on the tail of the probability distribution.
SECOND_DEPARTMENT_THRESHOLD = 0.25
REFUND_THRESHOLD = 0.5

# Busy queue -> a shared retry budget that honors the server's
# retry-after header instead of a hand-rolled backoff loop.
_RETRY_POLICY = RetryPolicy(
    max_retries=5,
    backoff_initial=0.5,
    backoff_max=20.0,
    respect_retry_after=True,
)

# One client, reused across calls (and threads) for the life of the process.
_client = TypeSafeClient(model=MODEL, retry=_RETRY_POLICY)


@dataclass
class RoutingDecision:
    department: str
    department_confidence: float
    secondary_department: str | None
    severity_label: str
    severity_score: float
    severity_confidence: float
    probability_most_severe: float
    refund_requested: bool
    refund_probability: float
    model: str
    input_tokens: int


def triage_ticket(ticket_text: str, *, client: TypeSafeClient = _client) -> RoutingDecision:
    """Classify a support ticket and return a routing decision.

    Raises TypeSafeError (and subclasses) if Jev is unreachable or the
    shared rate limit's retry budget is exhausted; callers on a queue
    should let that surface as a redelivery rather than swallowing it.
    """
    try:
        response = client.system_one(
            state={"ticket": ticket_text},
            questions={
                "department": Choice(
                    instructions="Which department should handle `ticket`?",
                    criteria=DEPARTMENTS,
                ),
                "severity": Score(
                    instructions="How severe is the problem described in `ticket`?",
                    criteria=SEVERITY_LEVELS,
                ),
                "refund": Noul(
                    instructions=(
                        "Is the customer asking for a refund, credit, chargeback, "
                        "or their money back in `ticket`?"
                    ),
                ),
            },
        )
    except TypeSafeRateLimitError as exc:
        logger.warning(
            "Jev rate limit exhausted after retries (retry_after_ms=%s)",
            exc.retry_after_ms,
        )
        raise
    except TypeSafeAPIError:
        logger.exception("Jev triage request failed")
        raise

    department = response.choices["department"]
    severity = response.scores["severity"]
    refund = response.nouls["refund"]

    ranked = sorted(department.probabilities.items(), key=lambda kv: kv[1], reverse=True)
    secondary_department = None
    if len(ranked) > 1:
        second_name, second_prob = ranked[1]
        if second_prob >= SECOND_DEPARTMENT_THRESHOLD:
            secondary_department = second_name

    nearest_level = min(round(severity.score), MOST_SEVERE_LEVEL)

    return RoutingDecision(
        department=department.choice,
        department_confidence=department.confidence,
        secondary_department=secondary_department,
        severity_label=severity.legend[nearest_level],
        severity_score=severity.score,
        severity_confidence=severity.confidence,
        probability_most_severe=severity.probabilities[MOST_SEVERE_LEVEL],
        refund_requested=refund.noul >= REFUND_THRESHOLD,
        refund_probability=refund.noul,
        model=response.model,
        input_tokens=response.usage.input_tokens,
    )
