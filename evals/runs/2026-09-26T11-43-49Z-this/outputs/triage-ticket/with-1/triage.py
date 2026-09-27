"""Support ticket triage backed by TypeSafe Jev (System One API).

Docs: https://docs.typesafe.ai
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from typesafe_sdk import (
    Choice,
    Noul,
    RetryPolicy,
    Score,
    TypeSafeClient,
)

# Departments a ticket can be routed to. Adjacent departments get a
# `what` / `not_for` pair (per Jev's guidance) so the model doesn't
# confuse them, e.g. "billing" vs. "a paid feature that's broken".
DEPARTMENTS = {
    "technical": {
        "what": "Bugs, errors, crashes, broken features, integration or performance problems.",
        "not_for": "Billing questions or how-to questions where nothing is malfunctioning.",
    },
    "billing": {
        "what": "Charges, invoices, payments, subscription plans, pricing.",
        "not_for": "A feature not working, even on a paid plan.",
    },
    "account": {
        "what": "Login, password reset, account access, permissions, profile data.",
        "not_for": "Payment or subscription-plan questions.",
    },
    "shipping": {
        "what": "Physical delivery: tracking, lost or damaged packages, delivery delays.",
        "not_for": "Digital access or software issues.",
    },
    "sales": {
        "what": "Pre-purchase questions, upgrades, quotes, new orders.",
        "not_for": "Support for something already purchased.",
    },
    "other": None,
}

# Each severity level describes a single situation on one dimension
# (customer impact), not a vague degree, so Jev can judge each in isolation.
SEVERITY_LEVELS = [
    "Cosmetic or informational: no impact on using the product.",
    "Minor inconvenience: a workaround exists and the customer can proceed.",
    "Major problem: a core feature is unusable and there is no workaround.",
    "Critical: outage, data loss, security exposure, or the customer cannot use the product at all.",
]
_MOST_SEVERE_LEVEL = len(SEVERITY_LEVELS) - 1

# A second department is only worth notifying if it's a real contender,
# not just noise (patterns.md: "notify a second option above ~0.25").
SECONDARY_DEPARTMENT_THRESHOLD = 0.25

# Noul uncertainty band: below 0.30 = no, above 0.70 = yes. Anything in
# between is genuinely ambiguous, so callers get the raw probability too.
REFUND_THRESHOLD = 0.70

_client: Optional[TypeSafeClient] = None


def _get_client() -> TypeSafeClient:
    """Return the module-level TypeSafeClient, creating it on first use.

    One client is reused for every call (and is safe to share across
    threads), since the queue this runs on will call `triage_ticket` at
    high volume. `RetryPolicy` covers 429s and 5xxs with backoff so a busy
    queue backs off automatically instead of failing tickets outright.
    """
    global _client
    if _client is None:
        _client = TypeSafeClient(
            retry=RetryPolicy(
                max_retries=5,
                backoff_initial=0.5,
                backoff_max=20.0,
                respect_retry_after=True,
            ),
            timeout=10.0,
        )
    return _client


@dataclass
class RoutingDecision:
    department: str
    secondary_department: Optional[str]
    severity_level: str
    severity_score: float
    severity_top_probability: float
    refund_requested: bool
    refund_probability: float
    model: str
    input_tokens: int


def triage_ticket(ticket_text: str, *, client: Optional[TypeSafeClient] = None) -> RoutingDecision:
    """Classify a support ticket and return a routing decision.

    Issues one System One request with every question the routing decision
    needs (department, severity, refund intent) so they run in parallel in
    a single call rather than three round trips.

    Raises whatever `TypeSafeAPIError` subclass the SDK raises once its
    built-in retries are exhausted (e.g. `TypeSafeRateLimitError`); the
    caller on the queue should requeue the ticket rather than drop it.
    """
    client = client or _get_client()

    response = client.system_one(
        state={"ticket": {"text": ticket_text}},
        questions={
            "department": Choice(
                instructions="Which department should handle `ticket.text`?",
                criteria=DEPARTMENTS,
            ),
            "severity": Score(
                instructions="How severe is the problem described in `ticket.text` for the customer?",
                criteria=SEVERITY_LEVELS,
            ),
            "refund": Noul(
                instructions="Is the customer in `ticket.text` asking for a refund or their money back?",
            ),
        },
    )

    department_answer = response.choices["department"]
    severity_answer = response.scores["severity"]
    refund_answer = response.nouls["refund"]

    department = department_answer.choice
    secondary_department = next(
        (
            name
            for name, probability in sorted(
                department_answer.probabilities.items(), key=lambda kv: kv[1], reverse=True
            )
            if name != department and probability > SECONDARY_DEPARTMENT_THRESHOLD
        ),
        None,
    )

    # Nearest whole level for a human-readable label (patterns.md: route on
    # the nearest Score level rather than interpolating a magnitude).
    nearest_level = min(int(severity_answer.score + 0.5), _MOST_SEVERE_LEVEL)

    return RoutingDecision(
        department=department,
        secondary_department=secondary_department,
        severity_level=severity_answer.legend[nearest_level],
        severity_score=severity_answer.score,
        severity_top_probability=severity_answer.probabilities.get(_MOST_SEVERE_LEVEL, 0.0),
        refund_requested=refund_answer.noul > REFUND_THRESHOLD,
        refund_probability=refund_answer.noul,
        model=response.model,
        input_tokens=response.usage.input_tokens,
    )
