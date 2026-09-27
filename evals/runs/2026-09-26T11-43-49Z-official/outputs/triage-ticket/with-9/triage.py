"""Support ticket triage powered by TypeSafe's Jev model (System One API)."""

from __future__ import annotations

from dataclasses import dataclass

from typesafe_sdk import (
    Choice,
    Noul,
    RetryPolicy,
    Score,
    TypeSafeAPIConnectionError,
    TypeSafeAPITimeoutError,
    TypeSafeClient,
    TypeSafeRateLimitError,
)

DEPARTMENTS = {
    "billing": "Charges, invoices, payments, subscriptions, and pricing questions.",
    "technical_support": "Bugs, errors, crashes, or features not working as expected.",
    "shipping": "Delivery delays, tracking, or lost or damaged packages.",
    "account_security": "Login issues, password resets, or suspicious account activity.",
    "sales": "Upgrades, new purchases, or questions before buying.",
    "general": "Anything that doesn't fit the other departments.",
}

# Ordered low to high; the model scores the ticket against each independently.
SEVERITY_LEVELS = [
    "Minor: a question or cosmetic issue with no impact on using the product or service.",
    "Moderate: a feature is degraded or inconvenient, but a workaround exists.",
    "Major: a core feature is broken with no workaround, blocking normal use.",
    "Critical: complete outage, data loss, security breach, incorrect charge, or safety risk.",
]

# A ticket only gets a second department if the runner-up is plausible, not just nonzero.
SECOND_DEPARTMENT_MIN_PROBABILITY = 0.2

REFUND_PROBABILITY_THRESHOLD = 0.5

# Busier and more patient than the SDK default (max_retries=2, timeout=30s) since
# a queue worker can afford to wait out a 429 rather than fail the ticket.
_RETRY_POLICY = RetryPolicy(
    max_retries=5,
    backoff_initial=1.0,
    backoff_max=20.0,
    timeout=60.0,
)

_client = TypeSafeClient(retry=_RETRY_POLICY)


class TriageUnavailable(Exception):
    """Jev couldn't be reached after retries; the ticket should be requeued."""


@dataclass(frozen=True)
class TriageDecision:
    department: str
    second_department: str | None
    severity_level: int
    severity_label: str
    probability_most_severe: float
    refund_requested: bool
    refund_probability: float


def triage_ticket(text: str, *, client: TypeSafeClient = _client) -> TriageDecision:
    """Classify a support ticket's department, severity, and refund intent via Jev."""
    try:
        response = client.system_one(
            state={"ticket_text": text},
            questions={
                "department": Choice(
                    instructions="Which department should handle this support ticket?",
                    criteria=DEPARTMENTS,
                ),
                "severity": Score(
                    instructions="How severe is the customer's problem?",
                    criteria=SEVERITY_LEVELS,
                ),
                "refund_requested": Noul(
                    instructions="Is the customer explicitly asking for a refund or their money back?",
                ),
            },
        )
    except (TypeSafeRateLimitError, TypeSafeAPIConnectionError, TypeSafeAPITimeoutError) as exc:
        raise TriageUnavailable(
            "Jev is rate-limited or unreachable after retries; requeue this ticket."
        ) from exc

    department_answer = response.choices["department"]
    severity_answer = response.scores["severity"]
    refund_answer = response.nouls["refund_requested"]

    ranked_departments = sorted(
        department_answer.probabilities.items(), key=lambda item: item[1], reverse=True
    )
    second_name, second_probability = ranked_departments[1]
    second_department = (
        second_name if second_probability >= SECOND_DEPARTMENT_MIN_PROBABILITY else None
    )

    severity_level = max(severity_answer.probabilities, key=severity_answer.probabilities.get)
    severity_level = int(severity_level)
    max_severity_level = len(SEVERITY_LEVELS) - 1

    return TriageDecision(
        department=department_answer.choice,
        second_department=second_department,
        severity_level=severity_level,
        severity_label=SEVERITY_LEVELS[severity_level],
        probability_most_severe=severity_answer.probabilities[str(max_severity_level)],
        refund_requested=refund_answer.noul >= REFUND_PROBABILITY_THRESHOLD,
        refund_probability=refund_answer.noul,
    )
