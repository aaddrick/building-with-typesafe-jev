"""Support-ticket triage backed by typesafe.ai's Jev model (System One API).

One `system_one` call per ticket asks every question we might need
(department, severity, refund) in parallel, then plain Python turns the
answers into a routing decision. See:
  https://docs.typesafe.ai/concepts/system-one
  https://docs.typesafe.ai/patterns/intent-routing
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from typesafe_sdk import (
    Choice,
    Noul,
    RetryPolicy,
    Score,
    TypeSafeClient,
    TypeSafeError,
)

# Pinned so tuned thresholds below don't drift if `jev-latest` moves to a new
# model version.
MODEL = "jev-1.13.0"

# --- Questions -------------------------------------------------------------
# Department names double as Choice keys sent to the model and as the
# strings this module returns, so keep them stable.
DEPARTMENTS = {
    "billing": "Payments, charges, invoices, subscriptions, refunds.",
    "technical": "The product is broken, erroring, or not working as documented.",
    "account": "Login, password, profile, permissions, account access.",
    "shipping": "Order fulfillment, delivery, tracking, lost or damaged packages.",
    "sales": "Buying, upgrading, pricing questions, or a pre-purchase question.",
    "other": "Does not clearly fit any department above.",
}

# Each level describes one concrete situation, not a point on a "how bad"
# scale, per the skill's Score-writing rule: levels are judged independently.
SEVERITY_LEVELS = [
    "Cosmetic or minor issue; does not block using the product.",
    "A feature is broken or a task is harder than it should be, but a workaround exists.",
    "A feature is broken with no workaround, blocking part of the customer's work.",
    "Total outage, data loss, security issue, or something broken for many customers at once.",
]
MOST_SEVERE_INDEX = len(SEVERITY_LEVELS) - 1

QUESTIONS = {
    "department": Choice(
        instructions=(
            "Which department should handle `ticket.text`? Judge only what "
            "the customer wrote, not how you'd personally categorize it."
        ),
        criteria=DEPARTMENTS,
    ),
    "severity": Score(
        instructions="How severe is the problem described in `ticket.text`?",
        criteria=SEVERITY_LEVELS,
    ),
    "refund": Noul(
        instructions="Does `ticket.text` ask for a refund, chargeback, or money back?",
    ),
}

# --- Thresholds (tune on labeled tickets; see docs.typesafe.ai/patterns/confidence-routing) --
SECOND_DEPARTMENT_MIN_PROBABILITY = 0.25  # cookbook default for "also notify"
DEPARTMENT_ABSTAIN_CONFIDENCE = 0.60      # below this, treat routing as uncertain
REFUND_YES = 0.70
REFUND_NO = 0.30


class TriageUnavailable(Exception):
    """Raised when Jev can't be reached after retries.

    Callers on a busy queue should catch this and requeue the ticket
    (e.g. with their own backoff) rather than losing it or crashing the
    whole worker.
    """


@dataclass(frozen=True)
class RoutingDecision:
    ticket_text: str
    department: str
    department_confidence: float
    secondary_department: Optional[str]
    severity_label: str
    severity_score: float
    probability_most_severe: float
    wants_refund: bool
    refund_probability: float
    needs_human_review: bool
    review_reasons: tuple[str, ...]
    model: str
    request_id: Optional[str]


@lru_cache(maxsize=1)
def _client() -> TypeSafeClient:
    # One client, reused across calls/threads, per the SDK's lifecycle
    # guidance -- don't construct one per request.
    #
    # A busy queue mostly needs to survive normal rate limiting, so retry
    # 429/5xx with backoff and honor `Retry-After` instead of hand-rolling
    # a retry loop. If the retry budget still runs out, `system_one` raises
    # and `triage_ticket` turns that into `TriageUnavailable` so the caller
    # can requeue.
    retry = RetryPolicy(
        max_retries=5,
        backoff_initial=0.5,
        backoff_max=20.0,
        backoff_jitter=0.25,
        respect_retry_after=True,
    )
    return TypeSafeClient(model=MODEL, retry=retry)


def triage_ticket(ticket_text: str) -> RoutingDecision:
    """Classify one support ticket into a routing decision.

    Raises:
        TriageUnavailable: Jev could not be reached after retries (rate
            limited, overloaded, or a connection/timeout failure).
    """
    try:
        response = _client().system_one(
            state={"ticket": {"text": ticket_text}},
            questions=QUESTIONS,
        )
    except TypeSafeError as exc:
        raise TriageUnavailable(f"Jev request failed: {exc}") from exc

    department_answer = response.choices["department"]
    severity_answer = response.scores["severity"]
    refund_answer = response.nouls["refund"]

    review_reasons = []

    department = department_answer.choice
    if department_answer.confidence < DEPARTMENT_ABSTAIN_CONFIDENCE:
        review_reasons.append(
            f"low department confidence ({department_answer.confidence:.2f})"
        )

    # A second department worth notifying: the runner-up option, if it's
    # carrying enough probability to matter (patterns.md: "Belongs to two
    # categories? Route to choice, and notify a second option whose
    # probability is above about 0.25.").
    secondary_department = None
    runner_up = max(
        (
            (name, probability)
            for name, probability in department_answer.probabilities.items()
            if name != department
        ),
        key=lambda item: item[1],
        default=None,
    )
    if runner_up is not None and runner_up[1] > SECOND_DEPARTMENT_MIN_PROBABILITY:
        secondary_department = runner_up[0]

    severity_index = min(round(severity_answer.score), MOST_SEVERE_INDEX)
    probability_most_severe = severity_answer.probabilities[MOST_SEVERE_INDEX]

    refund_probability = refund_answer.noul
    wants_refund = refund_probability >= 0.5
    if REFUND_NO < refund_probability < REFUND_YES:
        review_reasons.append(f"ambiguous refund signal ({refund_probability:.2f})")

    return RoutingDecision(
        ticket_text=ticket_text,
        department=department,
        department_confidence=department_answer.confidence,
        secondary_department=secondary_department,
        severity_label=SEVERITY_LEVELS[severity_index],
        severity_score=severity_answer.score,
        probability_most_severe=probability_most_severe,
        wants_refund=wants_refund,
        refund_probability=refund_probability,
        needs_human_review=bool(review_reasons),
        review_reasons=tuple(review_reasons),
        model=response.model,
        request_id=response.request_id,
    )


if __name__ == "__main__":
    decision = triage_ticket(
        "I've been charged twice for my subscription this month and the "
        "app still crashes every time I try to export a report. I want my "
        "money back."
    )
    print(decision)
