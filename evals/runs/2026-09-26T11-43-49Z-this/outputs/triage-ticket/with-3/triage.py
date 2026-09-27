"""Support-ticket triage backed by TypeSafe's Jev model (System One API).

Live API testing was off for this session (no TYPESAFE_API_KEY configured), so this
was written against docs.typesafe.ai's published request/response shapes rather than
verified with real calls. Run a few live calls before trusting it in production.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Optional

from typesafe_sdk import (
    Choice,
    Noul,
    NoulCriteria,
    RetryPolicy,
    Score,
    TypeSafeClient,
    TypeSafeRateLimitError,
)

# --- Tunables: questions, thresholds, and weights live here so they're easy to review. ---

MODEL = "jev-1.13.0"  # pinned so threshold tuning below doesn't silently drift

# Full department roster. Each option is written as what/not_for/examples because a
# couple of these pairs (billing vs. sales, technical vs. account) are easy to confuse.
DEPARTMENT_CRITERIA = {
    "billing": {
        "what": "Charges, invoices, payments, refunds, or the price of a plan.",
        "not_for": "Login/access trouble (that's account) or a broken feature (that's technical).",
        "examples": ["I was charged twice", "Why is this month's invoice higher?"],
    },
    "technical": {
        "what": "The product is broken, erroring, or not behaving as documented.",
        "not_for": "The cost of something (billing) or upgrading/buying more (sales).",
        "examples": ["The export button throws a 500 error", "Sync stopped working after the update"],
    },
    "account": {
        "what": "Login, password reset, access, permissions, or team member management.",
        "not_for": "The cost of the account (billing) or a broken feature once logged in (technical).",
        "examples": ["I can't log in", "Please remove a teammate from our workspace"],
    },
    "sales": {
        "what": "Upgrading, downgrading, adding seats, or questions before purchase.",
        "not_for": "Disputing a charge that already happened (billing).",
        "examples": ["We want to add 20 more seats", "What's the difference between Pro and Enterprise?"],
    },
    "other": "Doesn't fit billing, technical, account, or sales.",
}

# Ordered, concrete situations (one dimension: how much the problem blocks the customer),
# not vague labels like "low/medium/high" -- Jev judges each level in isolation.
SEVERITY_LEVELS = [
    "Minor issue or question; nothing is broken and the customer can continue normally.",
    "A feature is broken or confusing, but a workaround exists and the customer can still get their work done.",
    "Core functionality is broken or inaccessible, blocking the customer's work, with no workaround.",
    "Complete outage, data loss, or a security/payment-safety issue affecting the customer right now.",
]
MOST_SEVERE_LEVEL = len(SEVERITY_LEVELS) - 1

# A second department is only worth surfacing when it holds real probability mass.
SECOND_DEPARTMENT_PROBABILITY_THRESHOLD = 0.25

# Simple yes/no cutoff for the refund Noul. `refund_probability` is still returned
# on the decision so a caller can apply a tighter band (e.g. route 0.3-0.7 to a human)
# without another API call.
REFUND_YES_THRESHOLD = 0.5

QUESTIONS = {
    "department": Choice(
        instructions="Which department should handle this support ticket, based on `ticket_text`?",
        criteria=DEPARTMENT_CRITERIA,
    ),
    "severity": Score(
        instructions="How severe is the customer's problem described in `ticket_text`?",
        criteria=SEVERITY_LEVELS,
    ),
    "refund": Noul(
        instructions="Does `ticket_text` ask for a refund, chargeback, or the customer's money back?",
        criteria=NoulCriteria(
            true="Explicitly requests money back, a refund, or a chargeback.",
            false="No request for money back, even if the customer is unhappy.",
        ),
    ),
}


@dataclass(frozen=True)
class RoutingDecision:
    department: str
    department_confidence: float
    secondary_department: Optional[str]

    severity_level: str
    severity_score: float
    severity_confidence: float
    most_severe_probability: float

    refund_requested: bool
    refund_probability: float

    model: str
    request_id: Optional[str]


class TriageError(Exception):
    """Raised when Jev could not be reached or returned an unusable response."""


class TriageRateLimited(TriageError):
    """Raised when the rate limit was hit and retries were exhausted.

    A busy queue should catch this and requeue the ticket rather than drop it or
    crash the worker; `retry_after_ms` (when present) says how long to wait.
    """

    def __init__(self, retry_after_ms: Optional[int], cause: Exception):
        super().__init__(f"Jev rate limit exhausted (retry_after_ms={retry_after_ms})")
        self.retry_after_ms = retry_after_ms
        self.cause = cause


# One client for the whole process, shared across threads, built lazily so importing
# this module doesn't require TYPESAFE_API_KEY to be set until triage actually runs.
_client: Optional[TypeSafeClient] = None
_client_lock = threading.Lock()

# A busy queue means many workers hitting one key: retry harder than the SDK's
# defaults (max_retries=2) and always honor `retry-after` from a 429.
_RETRY_POLICY = RetryPolicy(
    max_retries=5,
    backoff_initial=0.5,
    backoff_max=20.0,
    backoff_jitter=0.25,
    respect_retry_after=True,
)


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = TypeSafeClient(model=MODEL, retry=_RETRY_POLICY)
    return _client


def close() -> None:
    """Release the shared client. Call once at process shutdown."""
    global _client
    with _client_lock:
        if _client is not None:
            _client.close()
            _client = None


def triage_ticket(ticket_text: str) -> RoutingDecision:
    """Classify one support ticket into a routing decision.

    Raises:
        TriageRateLimited: the rate limit was hit and the SDK's retries were exhausted.
            Meant to be caught by the queue worker so the ticket can be requeued.
        TriageError: any other failure talking to Jev.
    """
    client = _get_client()

    try:
        response = client.system_one(
            state={"ticket_text": ticket_text},
            questions=QUESTIONS,
        )
    except TypeSafeRateLimitError as exc:
        raise TriageRateLimited(exc.retry_after_ms, exc) from exc
    except Exception as exc:  # connection errors, 4xx/5xx after retries, etc.
        raise TriageError(f"Jev triage call failed: {exc}") from exc

    department = response.choices["department"]
    severity = response.scores["severity"]
    refund = response.nouls["refund"]

    secondary_department = None
    best_other_department, best_other_probability = None, 0.0
    for name, probability in department.probabilities.items():
        if name != department.choice and probability > best_other_probability:
            best_other_department, best_other_probability = name, probability
    if best_other_probability > SECOND_DEPARTMENT_PROBABILITY_THRESHOLD:
        secondary_department = best_other_department

    most_severe_probability = severity.probabilities.get(MOST_SEVERE_LEVEL, 0.0)

    return RoutingDecision(
        department=department.choice,
        department_confidence=department.confidence,
        secondary_department=secondary_department,
        severity_level=severity.legend[round(severity.score)],
        severity_score=severity.score,
        severity_confidence=severity.confidence,
        most_severe_probability=most_severe_probability,
        refund_requested=refund.noul >= REFUND_YES_THRESHOLD,
        refund_probability=refund.noul,
        model=response.model,
        request_id=response.request_id,
    )


if __name__ == "__main__":
    sample = (
        "I've been charged twice for my subscription this month and I want my money "
        "back immediately. Nobody has responded to my last two emails about this."
    )
    decision = triage_ticket(sample)
    print(decision)
    close()
