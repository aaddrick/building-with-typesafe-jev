"""Support-ticket triage using typesafe.ai's Jev model (System One API).

Asks Jev three parallel questions about a ticket's text -- which department
should handle it, how severe the problem is, and whether a refund is being
requested -- and turns the answers into a routing decision a queue worker
can act on.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from typesafe_sdk import (
    Choice,
    Noul,
    RetryPolicy,
    Score,
    TypeSafeClient,
    TypeSafeRateLimitError,
)

# Departments a ticket can be routed to, as a Choice question. Descriptions
# are shown to the model, not to callers -- adjust them to match the real
# department list of the support desk this is wired into.
DEFAULT_DEPARTMENTS: Mapping[str, str] = {
    "billing": "Payments, invoices, charges, subscription plans, refunds",
    "technical_support": "Bugs, errors, crashes, the product not working as expected, integrations",
    "shipping_logistics": "Order shipment, delivery, tracking, lost or delayed packages",
    "account_access": "Login issues, password resets, account security, permissions",
    "sales": "Pricing questions, upgrades, new purchases, demos",
    "general_inquiry": "Anything else that does not fit another department",
}

# Ordered low-to-high severity rubric for the Score question. The last
# level is treated as "most severe" when reporting its probability.
DEFAULT_SEVERITY_LEVELS: Sequence[str] = (
    "Minor: cosmetic issue or question with no impact on the customer's ability to use the product",
    "Moderate: a feature is degraded or inconvenient, but a workaround exists",
    "Major: a core feature is broken with no workaround, significantly disrupting the customer's use",
    "Critical: complete outage, data loss, security issue, or a problem affecting many customers or business-critical operations",
)

# A ticket runs through a busy queue, so retries need to be more patient
# than the SDK default and must respect the server's Retry-After hint.
QUEUE_RETRY_POLICY = RetryPolicy(
    max_retries=5,
    backoff_initial=0.5,
    backoff_max=10.0,
    respect_retry_after=True,
    timeout=30.0,
)

# Below this probability, a second-place department is considered noise
# rather than a genuine secondary candidate. Tune against real ticket data.
SECONDARY_DEPARTMENT_THRESHOLD = 0.25


class TicketTriageRateLimited(Exception):
    """Raised when Jev is still rate-limited after the retry budget is spent.

    Callers on a queue should catch this and redeliver the ticket later
    (after `retry_after_seconds` if known) instead of dropping it or
    crashing the worker.
    """

    def __init__(self, retry_after_seconds: float | None):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            f"Jev is rate-limited; retry after {retry_after_seconds}s"
            if retry_after_seconds is not None
            else "Jev is rate-limited; retry later"
        )


@dataclass
class TriageResult:
    department: str
    department_confidence: float
    secondary_department: str | None

    severity_label: str
    severity_score: float
    severity_confidence: float
    most_severe_probability: float

    refund_requested: bool
    refund_probability: float


def triage_ticket(
    text: str,
    *,
    client: TypeSafeClient | None = None,
    departments: Mapping[str, str] = DEFAULT_DEPARTMENTS,
    severity_levels: Sequence[str] = DEFAULT_SEVERITY_LEVELS,
    secondary_department_threshold: float = SECONDARY_DEPARTMENT_THRESHOLD,
) -> TriageResult:
    """Decide how to route a support ticket.

    Runs one System One request with three parallel questions (department,
    severity, refund request) and turns the answers into a `TriageResult`.

    Pass a shared `client` when calling this repeatedly from a queue worker
    so connections are reused; one is created and closed per call otherwise.
    """
    owns_client = client is None
    client = client or TypeSafeClient()
    try:
        try:
            response = client.system_one(
                state=text,
                questions={
                    "department": Choice(
                        instructions="Which department should handle this support ticket?",
                        criteria=departments,
                    ),
                    "severity": Score(
                        instructions="How severe is the problem described in this ticket?",
                        criteria=severity_levels,
                    ),
                    "refund_requested": Noul(
                        instructions="Is the customer explicitly asking for a refund, money back, or a reversed charge?",
                        criteria={
                            "true": "Explicitly asks for money back, a refund, or a charge reversal",
                            "false": "No mention of a refund or reimbursement",
                        },
                    ),
                },
                retry=QUEUE_RETRY_POLICY,
            )
        except TypeSafeRateLimitError as error:
            retry_after_seconds = (
                error.retry_after_ms / 1000 if error.retry_after_ms is not None else None
            )
            raise TicketTriageRateLimited(retry_after_seconds) from error
    finally:
        if owns_client:
            client.close()

    department_answer = response.choices()["department"]
    severity_answer = response.scores()["severity"]
    refund_answer = response.nouls()["refund_requested"]

    secondary_department = _secondary_department(
        department_answer.probabilities,
        primary=department_answer.choice,
        threshold=secondary_department_threshold,
    )

    top_level = len(severity_levels) - 1
    most_severe_probability = severity_answer.probabilities.get(
        top_level, severity_answer.probabilities.get(str(top_level), 0.0)
    )
    severity_label = severity_answer.legend.get(
        round(severity_answer.score), severity_answer.legend.get(str(round(severity_answer.score)))
    )

    return TriageResult(
        department=department_answer.choice,
        department_confidence=department_answer.confidence,
        secondary_department=secondary_department,
        severity_label=severity_label,
        severity_score=severity_answer.score,
        severity_confidence=severity_answer.confidence,
        most_severe_probability=most_severe_probability,
        refund_requested=refund_answer.noul >= 0.5,
        refund_probability=refund_answer.noul,
    )


def _secondary_department(
    probabilities: Mapping[str, float], *, primary: str, threshold: float
) -> str | None:
    runner_up = max(
        (item for item in probabilities.items() if item[0] != primary),
        key=lambda item: item[1],
        default=None,
    )
    if runner_up is not None and runner_up[1] >= threshold:
        return runner_up[0]
    return None
