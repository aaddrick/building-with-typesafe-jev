"""Read a customer email with typesafe.ai's Jev model.

Jev (docs.typesafe.ai) answers typed Choice/Score/Noul questions but does not count
or do date arithmetic reliably, so both facts below are assembled in code from many
small model judgments rather than asked of the model directly.
"""

from __future__ import annotations

import datetime
import re

from typesafe_sdk import Choice, Noul, TypeSafeClient

MODEL = "jev-latest"
YES_THRESHOLD = 0.5

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

_NOT_APPLICABLE = "Not applicable or not stated in the email."
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]


def _sentence_id(i: int) -> str:
    return f"S{i:03d}"


def _tag_sentences(sentences: list[str]) -> str:
    return "\n".join(f"{_sentence_id(i)}| {s}" for i, s in enumerate(sentences))


def _count_defective_products(client: TypeSafeClient, email_text: str) -> int:
    sentences = _split_sentences(email_text)
    if not sentences:
        return 0

    document = _tag_sentences(sentences)

    # One independent yes/no question per sentence, batched into a single call.
    flag_questions = {
        f"defect_{_sentence_id(i)}": Noul(
            instructions=(
                f"Does sentence {_sentence_id(i)} state that a specific product the "
                "customer purchased is defective, broken, damaged, or otherwise not "
                "working correctly?"
            ),
        )
        for i in range(len(sentences))
    }
    flag_answers = client.system_one(
        state=document, questions=flag_questions, model=MODEL
    ).answers
    flagged = [
        i
        for i in range(len(sentences))
        if flag_answers[f"defect_{_sentence_id(i)}"].noul >= YES_THRESHOLD
    ]

    if len(flagged) <= 1:
        return len(flagged)

    # Different sentences may complain about the same product, so merge sentences
    # that refer to the same product via pairwise checks before counting groups.
    pairs = [(i, j) for a, i in enumerate(flagged) for j in flagged[a + 1 :]]
    same_product_questions = {
        f"same_{_sentence_id(i)}_{_sentence_id(j)}": Noul(
            instructions=(
                f"Do sentences {_sentence_id(i)} and {_sentence_id(j)} describe a "
                "defect in the same product, as opposed to two different products?"
            ),
        )
        for i, j in pairs
    }
    same_answers = client.system_one(
        state=document, questions=same_product_questions, model=MODEL
    ).answers

    parent = {i: i for i in flagged}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, j in pairs:
        if same_answers[f"same_{_sentence_id(i)}_{_sentence_id(j)}"].noul >= YES_THRESHOLD:
            root_i, root_j = find(i), find(j)
            if root_i != root_j:
                parent[root_j] = root_i

    return len({find(i) for i in flagged})


def _extract_promised_delivery_date(
    client: TypeSafeClient, email_text: str, today: datetime.date
) -> datetime.date | None:
    role = "the delivery date the seller promised the customer"

    questions = {
        "mode": Choice(
            instructions=(
                f"How is {role} expressed in the email, if at all? 'absolute' means "
                "a calendar date naming a month; 'relative' means phrased relative to "
                "today (e.g. 'tomorrow', 'next Friday'); 'none' means no promised "
                "delivery date is stated."
            ),
            criteria={"absolute": None, "relative": None, "none": None},
        ),
        "month": Choice(
            instructions=f"If {role} is absolute, which month is it in?",
            criteria={name: None for name in MONTHS} | {"none": _NOT_APPLICABLE},
        ),
        "day": Choice(
            instructions=f"If {role} is absolute, which day of the month (1-31) is it?",
            criteria={str(d): None for d in range(1, 32)} | {"none": _NOT_APPLICABLE},
        ),
        "year": Choice(
            instructions=(
                f"If {role} is absolute and states a year, which year is it? 'none' "
                "if no year is stated."
            ),
            criteria={str(y): None for y in range(today.year - 1, today.year + 3)}
            | {"none": _NOT_APPLICABLE},
        ),
        "day_anchor": Choice(
            instructions=(
                f"If {role} is relative, which day does it refer to: 'today', "
                "'tomorrow', 'day_after' (the day after tomorrow), or 'weekday' (a "
                "named day of the week)?"
            ),
            criteria={
                "today": None,
                "tomorrow": None,
                "day_after": None,
                "weekday": None,
                "none": _NOT_APPLICABLE,
            },
        ),
        "weekday": Choice(
            instructions=f"If {role} names a day of the week, which one?",
            criteria={w: None for w in WEEKDAYS} | {"none": _NOT_APPLICABLE},
        ),
        "week_offset": Choice(
            instructions=(
                f"If {role} names a day of the week, is it 'current' (the coming "
                "occurrence, e.g. 'this Friday') or 'next' (the following week's "
                "occurrence, e.g. 'next Friday')?"
            ),
            criteria={"current": None, "next": None, "none": _NOT_APPLICABLE},
        ),
    }

    answers = client.system_one(state=email_text, questions=questions, model=MODEL).answers

    mode = answers["mode"].choice
    if mode == "absolute":
        month_name = answers["month"].choice
        day_str = answers["day"].choice
        year_str = answers["year"].choice
        if month_name == "none" or day_str == "none":
            return None
        month, day = MONTHS[month_name], int(day_str)
        if year_str == "none":
            resolved = datetime.date(today.year, month, day)
            if resolved < today - datetime.timedelta(days=31):
                resolved = datetime.date(today.year + 1, month, day)
            return resolved
        return datetime.date(int(year_str), month, day)

    if mode == "relative":
        anchor = answers["day_anchor"].choice
        if anchor == "today":
            return today
        if anchor == "tomorrow":
            return today + datetime.timedelta(days=1)
        if anchor == "day_after":
            return today + datetime.timedelta(days=2)
        if anchor == "weekday":
            weekday_name = answers["weekday"].choice
            if weekday_name == "none":
                return None
            days_ahead = (WEEKDAYS.index(weekday_name) - today.weekday()) % 7
            if answers["week_offset"].choice == "next":
                days_ahead += 7
            return today + datetime.timedelta(days=days_ahead)

    return None


def check_email(email_text: str, today: datetime.date) -> dict:
    """Report how many distinct products the customer says are defective, and
    whether the delivery date they were promised has already passed as of `today`.
    """
    with TypeSafeClient() as client:
        defective_product_count = _count_defective_products(client, email_text)
        promised_delivery_date = _extract_promised_delivery_date(client, email_text, today)

    return {
        "defective_product_count": defective_product_count,
        "promised_delivery_date": (
            promised_delivery_date.isoformat() if promised_delivery_date else None
        ),
        "delivery_date_passed": (
            promised_delivery_date < today if promised_delivery_date else None
        ),
    }
