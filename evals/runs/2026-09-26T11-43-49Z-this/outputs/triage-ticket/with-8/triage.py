"""Support-ticket triage using TypeSafe's Jev model (System One API).

Requires: pip install typesafe-sdk
Requires: TYPESAFE_API_KEY set in the environment.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from typesafe_sdk import (
    Choice,
    Noul,
    NoulCriteria,
    RetryPolicy,
    Score,
    TypeSafeAPIError,
    TypeSafeClient,
    TypeSafeError,
    TypeSafeRateLimitError,
)

logger = logging.getLogger(__name__)

# --- Tunables: review these against labeled tickets, not just intuition. ---

# Departments a ticket can be routed to. Keep descriptions distinct enough
# that Jev can tell adjacent ones apart (e.g. billing vs. sales).
DEPARTMENTS: dict[str, str] = {
    "billing": "Charges, invoices, payments, subscription plans, billing disputes.",
    "technical": "Bugs, errors, crashes, broken features, performance, outages.",
    "account": "Login, password reset, account access, profile or security settings.",
    "shipping": "Order shipping, delivery delays, tracking, lost or damaged packages.",
    "sales": "Pre-purchase questions, pricing, upgrades, new plans, demos.",
    "other": "Does not clearly fit any department above.",
}

# Score levels describe situations, not degrees (one dimension each).
SEVERITY_LEVELS: list[str] = [
    "No functional impact: cosmetic issue, typo, or a question with no blocked task.",
    "Minor problem: a feature is inconvenient or slow, but a workaround exists "
    "and the customer can still get their task done.",
    "Major problem: a feature the customer needs is broken with no workaround, "
    "blocking a specific task.",
    "Critical: the customer cannot use the product at all, data appears lost, "
    "or money was charged incorrectly with no way to resolve it themselves.",
]
MOST_SEVERE_LEVEL = len(SEVERITY_LEVELS) - 1

# Second department is reported only when it is a real contender.
SECOND_DEPARTMENT_PROBABILITY_FLOOR = 0.25
# Below this top probability, treat the department pick as too close to call.
DEPARTMENT_ABSTAIN_FLOOR = 0.60
# Noul band (from TypeSafe's own cookbooks): <0.30 no, 0.30-0.70 uncertain, >0.70 yes.
REFUND_YES_FLOOR = 0.70
REFUND_UNCERTAIN_FLOOR = 0.30

MODEL = "jev-1.13.0"


@dataclass
class RoutingDecision:
    department: str | None
    secondary_department: str | None
    severity_level: int | None
    severity_label: str | None
    probability_most_severe: float | None
    refund_requested: bool | None
    refund_probability: float | None
    needs_human_review: bool
    model: str | None
    error: str | None = None


# One client, reused across calls (and across threads, per the SDK docs).
# Keep worker concurrency around 8 or fewer against a single shared API key.
_client: TypeSafeClient | None = None


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        _client = TypeSafeClient(
            model=MODEL,
            timeout=15.0,
            retry=RetryPolicy(
                max_retries=6,
                backoff_initial=0.5,
                backoff_max=20.0,
                backoff_jitter=0.25,
                http_statuses=(429, 500, 502, 503, 529),
                respect_retry_after=True,
            ),
        )
    return _client


def _fallback_decision(reason: str) -> RoutingDecision:
    """Used when Jev can't be reached even after retries.

    Routes conservatively to a human queue instead of guessing, so a rate
    limit or outage degrades the queue rather than misrouting tickets.
    """
    logger.warning("ticket triage falling back to human review: %s", reason)
    return RoutingDecision(
        department=None,
        secondary_department=None,
        severity_level=None,
        severity_label=None,
        probability_most_severe=None,
        refund_requested=None,
        refund_probability=None,
        needs_human_review=True,
        model=None,
        error=reason,
    )


def triage_ticket(ticket_text: str, *, client: TypeSafeClient | None = None) -> RoutingDecision:
    """Classify a support ticket and return a routing decision.

    Runs a single System One call with every question the router needs
    (department, severity, refund intent) so branching in this function
    costs no extra latency or requests.
    """
    if not ticket_text or not ticket_text.strip():
        raise ValueError("ticket_text must be a non-empty string")

    client = client or _get_client()
    state = {"ticket": {"text": ticket_text}}

    questions = {
        "department": Choice(
            instructions="Which department should handle `ticket.text`? "
            "Pick the single best match.",
            criteria=DEPARTMENTS,
        ),
        "severity": Score(
            instructions="How severe is the customer's problem described in `ticket.text`?",
            criteria=SEVERITY_LEVELS,
        ),
        "refund": Noul(
            instructions="Does `ticket.text` ask for a refund, credit, chargeback, "
            "or money back?",
            criteria=NoulCriteria(
                true="Explicitly or implicitly asks to get money back for a charge or purchase.",
                false="No request for money back.",
            ),
        ),
    }

    try:
        response = client.system_one(state=state, questions=questions)
    except TypeSafeRateLimitError as exc:
        return _fallback_decision(f"rate limited, retry_after_ms={exc.retry_after_ms}")
    except (TypeSafeAPIError, TypeSafeError) as exc:
        return _fallback_decision(f"{type(exc).__name__}: {exc}")

    department_answer = response.choices["department"]
    severity_answer = response.scores["severity"]
    refund_answer = response.nouls["refund"]

    top_department = department_answer.choice
    top_probability = department_answer.probabilities[top_department]

    secondary_department = None
    ranked = sorted(
        department_answer.probabilities.items(), key=lambda kv: kv[1], reverse=True
    )
    if len(ranked) > 1:
        second_name, second_probability = ranked[1]
        if second_probability >= SECOND_DEPARTMENT_PROBABILITY_FLOOR:
            secondary_department = second_name

    probability_most_severe = severity_answer.probabilities[MOST_SEVERE_LEVEL]

    refund_probability = refund_answer.noul
    refund_requested = refund_probability >= REFUND_YES_FLOOR

    needs_human_review = (
        top_probability < DEPARTMENT_ABSTAIN_FLOOR
        or REFUND_UNCERTAIN_FLOOR <= refund_probability < REFUND_YES_FLOOR
    )

    logger.info(
        "ticket triaged: department=%s (%.2f) severity=%d refund=%.2f model=%s",
        top_department,
        top_probability,
        severity_answer.score,
        refund_probability,
        response.model,
    )

    return RoutingDecision(
        department=top_department,
        secondary_department=secondary_department,
        severity_level=int(round(severity_answer.score)),
        severity_label=severity_answer.legend[int(round(severity_answer.score))],
        probability_most_severe=probability_most_severe,
        refund_requested=refund_requested,
        refund_probability=refund_probability,
        needs_human_review=needs_human_review,
        model=response.model,
    )


if __name__ == "__main__":
    example = (
        "I was charged twice for my subscription this month and the app still "
        "crashes every time I try to export a report. I want my money back."
    )
    decision = triage_ticket(example)
    print(decision)
