"""Support-ticket triage using TypeSafe's Jev model (System One API).

One `system_one` call asks every question the router might need (speculative
fan-out): which department owns the ticket, how severe the problem is, and
whether the customer wants a refund. Code combines the answers into a single
routing decision.
"""

from __future__ import annotations

from dataclasses import dataclass

from typesafe_sdk import (
    Choice,
    Noul,
    NoulCriteria,
    RetryPolicy,
    Score,
    TypeSafeAPIError,
    TypeSafeClient,
    TypeSafeRateLimitError,
)

# Pinned so the thresholds below stay valid; bump deliberately and re-tune.
MODEL = "jev-1.13.0"

DEPARTMENTS = {
    "billing": "Charges, invoices, payments, subscriptions, pricing disputes.",
    "technical": "The product is broken, erroring, or behaving unexpectedly.",
    "account": "Login, password, account access, or profile settings.",
    "shipping": "Order fulfillment, delivery, tracking, or returns of physical goods.",
    "sales": "Questions about upgrading, purchasing, or comparing plans.",
    "other": "Does not fit any department above.",
}

SEVERITY_LEVELS = [
    "Minor: a question or cosmetic issue, no impact on using the product.",
    "Moderate: a feature is broken or degraded, but a workaround exists.",
    "Major: a core feature is unusable and there is no workaround.",
    "Critical: total outage, data loss, security exposure, or safety issue.",
]
MOST_SEVERE_INDEX = len(SEVERITY_LEVELS) - 1

# A second department is only worth notifying if it's a real contender.
SECONDARY_DEPARTMENT_THRESHOLD = 0.25

# Noul band from the cookbooks: a single 0.5 cutoff flips on noise.
REFUND_YES_THRESHOLD = 0.70
REFUND_NO_THRESHOLD = 0.30

# One client for the process's lifetime; do not construct one per ticket.
# The SDK already retries 429/5xx with backoff, so this only tunes budget
# and honors `retry-after` on a shared, busy key.
_client = TypeSafeClient(
    retry=RetryPolicy(
        max_retries=5,
        backoff_initial=0.5,
        backoff_max=20.0,
        respect_retry_after=True,
    ),
    timeout=30.0,
)


class TriageUnavailable(Exception):
    """Jev could not be reached after retries (still rate-limited, or down)."""


@dataclass
class TriageDecision:
    department: str
    department_confidence: float
    secondary_department: str | None
    severity_level: str
    severity_score: float
    severity_confidence: float
    most_severe_probability: float
    # None means the answer fell in the 0.30-0.70 band: too close to call,
    # send to a human rather than acting on a guess.
    refund_requested: bool | None
    refund_probability: float
    model: str
    request_id: str


def triage_ticket(ticket_text: str) -> TriageDecision:
    """Decide which department a ticket belongs to, how severe it is, and
    whether the customer wants a refund.

    Raises TriageUnavailable if Jev is still rate-limited or unreachable
    after the client's built-in retries.
    """
    try:
        response = _client.system_one(
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
                    instructions="Is the customer in `ticket` asking for a refund?",
                    criteria=NoulCriteria(
                        true="Explicitly asks for money back, a refund, a chargeback, "
                        "or cancellation with reimbursement.",
                        false="No request to get money back.",
                    ),
                ),
            },
            model=MODEL,
        )
    except TypeSafeRateLimitError as exc:
        raise TriageUnavailable(
            f"rate-limited after retries (retry_after_ms={exc.retry_after_ms})"
        ) from exc
    except TypeSafeAPIError as exc:
        raise TriageUnavailable(f"request failed: {exc}") from exc

    department = response.choices["department"]
    severity = response.scores["severity"]
    refund = response.nouls["refund"]

    ranked = sorted(department.probabilities.items(), key=lambda kv: kv[1], reverse=True)
    secondary_department = None
    if len(ranked) > 1:
        second_label, second_probability = ranked[1]
        if second_probability >= SECONDARY_DEPARTMENT_THRESHOLD:
            secondary_department = second_label

    severity_index = min(int(severity.score + 0.5), MOST_SEVERE_INDEX)

    if refund.noul >= REFUND_YES_THRESHOLD:
        refund_requested = True
    elif refund.noul <= REFUND_NO_THRESHOLD:
        refund_requested = False
    else:
        refund_requested = None

    return TriageDecision(
        department=department.choice,
        department_confidence=department.confidence,
        secondary_department=secondary_department,
        severity_level=severity.legend[severity_index],
        severity_score=severity.score,
        severity_confidence=severity.confidence,
        most_severe_probability=severity.probabilities[MOST_SEVERE_INDEX],
        refund_requested=refund_requested,
        refund_probability=refund.noul,
        model=response.model,
        request_id=response.request_id,
    )


def close_client() -> None:
    """Call at process shutdown to release the shared client's connections."""
    _client.close()
