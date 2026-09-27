"""Support-ticket triage using TypeSafe's Jev model (System One API)."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock, Semaphore
from typing import Optional

from typesafe_sdk import (
    Choice,
    Noul,
    RetryPolicy,
    Score,
    TypeSafeClient,
)

# Pin the version we tuned the thresholds below against.
MODEL = "jev-1.13.0"

DEPARTMENTS = {
    "billing": {
        "what": "Charges, invoices, payments, subscriptions, pricing, or refunds.",
        "examples": ["I was charged twice this month", "Can I get a discount on renewal?"],
    },
    "technical": {
        "what": "The product is broken, erroring, slow, or behaving unexpectedly.",
        "examples": ["The app crashes when I hit export", "Sync has been stuck for a day"],
    },
    "account": {
        "what": "Login, password, access, security, or account settings.",
        "examples": ["I can't reset my password", "My account got locked out"],
    },
    "sales": {
        "what": "Buying, upgrading, or asking about plans before purchasing.",
        "examples": ["What's included in the enterprise plan?"],
    },
    "other": {
        "what": "Anything that does not fit billing, technical, account, or sales.",
        "examples": [],
    },
}

# Each level is one situation on one dimension, judged on its own -- not "worse than
# the previous level" (see rule 7 of the Jev skill).
SEVERITY_LEVELS = [
    "Cosmetic issue or minor annoyance; the customer can keep working normally.",
    "A feature is impaired, but a workaround exists.",
    "A feature is completely broken for this customer, with no workaround.",
    "Critical: the product is unusable, data is lost or at risk, or many customers are affected.",
]
MOST_SEVERE_LEVEL = len(SEVERITY_LEVELS) - 1

# Thresholds, tuned starting points per the confidence-gated-routing pattern.
# Re-tune against labeled tickets before relying on them in production.
DEPARTMENT_CONFIDENCE_FLOOR = 0.5
SEVERITY_CONFIDENCE_FLOOR = 0.5
SECOND_DEPARTMENT_THRESHOLD = 0.25
REFUND_YES_THRESHOLD = 0.70
REFUND_NO_THRESHOLD = 0.30

_MAX_CONCURRENT_REQUESTS = 8  # shared-key rate limit starts biting above ~8 workers

_client: Optional[TypeSafeClient] = None
_client_lock = Lock()
_request_slots = Semaphore(_MAX_CONCURRENT_REQUESTS)


def _get_client() -> TypeSafeClient:
    """Return the process-wide client, creating it once and reusing it across calls."""
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = TypeSafeClient(
                    retry=RetryPolicy(
                        max_retries=6,
                        backoff_initial=1.0,
                        backoff_max=30.0,
                        backoff_jitter=0.25,
                        http_statuses={408, 429, 500, 502, 503, 504, 529},
                        respect_retry_after=True,
                        timeout=60.0,  # total retry budget, not just one attempt
                    ),
                    timeout=15.0,
                )
    return _client


@dataclass
class RoutingDecision:
    department: str
    department_confidence: float
    secondary_department: Optional[str]
    severity_level: int
    severity_label: str
    most_severe_probability: float
    severity_confidence: float
    refund_requested: Optional[bool]  # None means the ticket was too ambiguous to call
    refund_probability: float
    needs_human_review: bool
    model: str


def triage_ticket(ticket_text: str) -> RoutingDecision:
    """Classify a support ticket and return a routing decision.

    Runs one Jev System One call carrying every question the caller might need
    (department, severity, refund), then combines the typed answers in code.
    Retries on 429/5xx are handled by the shared client's RetryPolicy; a bounded
    semaphore caps concurrent requests so a busy queue doesn't trigger the rate
    limit in the first place.
    """
    client = _get_client()
    state = {"ticket": {"text": ticket_text}}

    questions = {
        "department": Choice(
            instructions="Which department should handle `ticket.text`?",
            criteria=dict(DEPARTMENTS),
        ),
        "severity": Score(
            instructions="How severe is the problem described in `ticket.text`?",
            criteria=SEVERITY_LEVELS,
        ),
        "refund": Noul(
            instructions="Does `ticket.text` ask for a refund, chargeback, or money back?",
        ),
    }

    with _request_slots:
        response = client.system_one(state=state, questions=questions, model=MODEL)

    department = response.choices["department"]
    severity = response.scores["severity"]
    refund = response.nouls["refund"]

    ranked_departments = sorted(
        department.probabilities.items(), key=lambda kv: kv[1], reverse=True
    )
    secondary_department = None
    if len(ranked_departments) > 1:
        name, probability = ranked_departments[1]
        if name != department.choice and probability >= SECOND_DEPARTMENT_THRESHOLD:
            secondary_department = name

    # Nearest-level routing (see the "route on the nearest score level" pattern):
    # the fractional score is for sorting/thresholds, not for interpolating meaning.
    severity_level = min(round(severity.score), MOST_SEVERE_LEVEL)

    if refund.noul >= REFUND_YES_THRESHOLD:
        refund_requested: Optional[bool] = True
    elif refund.noul <= REFUND_NO_THRESHOLD:
        refund_requested = False
    else:
        refund_requested = None

    needs_human_review = (
        department.confidence < DEPARTMENT_CONFIDENCE_FLOOR
        or severity.confidence < SEVERITY_CONFIDENCE_FLOOR
        or refund_requested is None
    )

    return RoutingDecision(
        department=department.choice,
        department_confidence=department.confidence,
        secondary_department=secondary_department,
        severity_level=severity_level,
        severity_label=severity.legend[severity_level],
        most_severe_probability=severity.probabilities[MOST_SEVERE_LEVEL],
        severity_confidence=severity.confidence,
        refund_requested=refund_requested,
        refund_probability=refund.noul,
        needs_human_review=needs_human_review,
        model=response.model,
    )


if __name__ == "__main__":
    decision = triage_ticket(
        "I've been charged twice for my subscription this month and the export "
        "button just spins forever. Please refund the duplicate charge."
    )
    print(decision)
