"""Support ticket triage using typesafe.ai's Jev model (System One API).

Classifies a ticket's department, severity, and refund intent in a single
System One call, returning a structured routing decision.
"""

from __future__ import annotations

from dataclasses import dataclass

from typesafe_sdk import (
    Choice,
    Noul,
    NoulCriteria,
    RetryPolicy,
    Score,
    TypeSafeClient,
    TypeSafeRateLimitError,
)

# Department names -> descriptions used for the Choice question. Adjust to
# match your own team structure.
DEFAULT_DEPARTMENTS = {
    "billing": "Payments, invoices, subscriptions, or pricing disputes",
    "technical": "Bugs, errors, integration failures, or things not working as documented",
    "account": "Login, access, permissions, or account settings",
    "sales": "Pre-purchase questions, upgrades, or new plans",
}

# Ordered low -> high; the last level is treated as "most severe".
SEVERITY_LEVELS = [
    "Cosmetic issue or minor annoyance with no functional impact",
    "Inconvenient but a workaround exists",
    "Key feature broken with no workaround",
    "Service unusable, data loss, or security/financial exposure",
]

# A ticket is only worth routing to a second department if that department's
# probability clears this bar; otherwise it's noise from a close call.
SECONDARY_DEPARTMENT_THRESHOLD = 0.25

# Below this probability we treat the refund question as "no".
REFUND_PROBABILITY_THRESHOLD = 0.5

_RETRY_POLICY = RetryPolicy(
    max_retries=5,
    http_statuses={429, 500, 502, 503, 504},
    respect_retry_after=True,
    timeout=30.0,
)

_client: TypeSafeClient | None = None


def _get_client() -> TypeSafeClient:
    """Lazily build a module-level client so repeated calls from a busy
    queue reuse the same connection instead of reconnecting every time."""
    global _client
    if _client is None:
        _client = TypeSafeClient(retry=_RETRY_POLICY)
    return _client


class TriageRateLimitedError(RuntimeError):
    """Raised when the Jev API is still rate-limiting us after the SDK's
    built-in retries are exhausted, so the caller can requeue the ticket."""

    def __init__(self, retry_after_ms: int | None):
        self.retry_after_ms = retry_after_ms
        super().__init__(
            f"Jev API rate limit exceeded; retry after {retry_after_ms}ms"
            if retry_after_ms is not None
            else "Jev API rate limit exceeded"
        )


@dataclass
class RoutingDecision:
    department: str
    department_probability: float
    secondary_department: str | None
    secondary_department_probability: float | None
    severity: str
    most_severe_probability: float
    refund_requested: bool
    refund_probability: float


def triage_ticket(
    ticket_text: str,
    *,
    departments: dict[str, str] = DEFAULT_DEPARTMENTS,
    client: TypeSafeClient | None = None,
) -> RoutingDecision:
    """Classify a support ticket and return a routing decision.

    Runs one System One call with three questions: which department should
    handle the ticket (with a second department named if the model finds one
    plausible), how severe the problem is (reported as the probability that
    it sits at the most severe level), and whether the customer wants a
    refund.
    """
    active_client = client or _get_client()

    try:
        response = active_client.system_one(
            state=ticket_text,
            questions={
                "department": Choice(
                    instructions="Which department should handle this support ticket?",
                    criteria=departments,
                ),
                "severity": Score(
                    instructions="How severe is the customer's problem?",
                    criteria=SEVERITY_LEVELS,
                ),
                "refund": Noul(
                    instructions="Is the customer asking for a refund, money back, or a charge reversal?",
                    criteria=NoulCriteria(
                        true="Explicitly or clearly implicitly requests a refund or reversed charge",
                        false="No request for money back, even if unhappy or asking for a replacement/fix",
                    ),
                ),
            },
        )
    except TypeSafeRateLimitError as exc:
        raise TriageRateLimitedError(exc.retry_after_ms) from exc

    department_answer = response.answers["department"]
    ranked_departments = sorted(
        department_answer.probabilities.items(), key=lambda item: item[1], reverse=True
    )
    top_department, top_probability = ranked_departments[0]
    secondary_department = None
    secondary_probability = None
    if len(ranked_departments) > 1:
        candidate, candidate_probability = ranked_departments[1]
        if candidate_probability >= SECONDARY_DEPARTMENT_THRESHOLD:
            secondary_department = candidate
            secondary_probability = candidate_probability

    severity_answer = response.answers["severity"]
    top_level = max(severity_answer.probabilities, key=severity_answer.probabilities.get)
    severity_label = severity_answer.legend[top_level]
    most_severe_level = max(severity_answer.probabilities)
    most_severe_probability = severity_answer.probabilities[most_severe_level]

    refund_probability = response.answers["refund"].noul

    return RoutingDecision(
        department=top_department,
        department_probability=top_probability,
        secondary_department=secondary_department,
        secondary_department_probability=secondary_probability,
        severity=severity_label,
        most_severe_probability=most_severe_probability,
        refund_requested=refund_probability >= REFUND_PROBABILITY_THRESHOLD,
        refund_probability=refund_probability,
    )
