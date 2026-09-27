"""Read a customer email with typesafe.ai's Jev model.

Reports how many distinct products the customer says are defective, and
whether the delivery date they were promised has already passed.
"""

import datetime
import re

from typesafe_sdk import Choice, Noul, TypeSafeClient

MODEL = "jev-1.13.0"

# Below this, a Noul answer is treated as "no".
DEFECT_THRESHOLD = 0.5
NEW_PRODUCT_THRESHOLD = 0.5

# Below this, the assembled delivery date is untrustworthy (cookbooks/date_extraction_cookbook).
DATE_REVIEW_BELOW = 0.60

MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
YEAR_WINDOW = list(range(1900, 2051))


def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s for s in sentences if s.strip()]


# --- how many different products the customer says are defective ---
#
# Counting is done in code (rule: keep counting out of the model). Stage 1
# asks one cheap Noul per sentence, in a single request, to find candidate
# sentences that report a defect. Stage 2 walks only those candidates in
# order and asks whether each names a product not already counted; this step
# must be sequential because each question needs the previous step's result.


def _find_defect_candidates(client: TypeSafeClient, sentences: list[str]) -> list[str]:
    if not sentences:
        return []
    questions = {
        f"defect_{i}": Noul(
            instructions=(
                f"Does `sentences[{i}]` state that a specific product is defective, "
                "broken, damaged, faulty, or otherwise not working?"
            ),
        )
        for i in range(len(sentences))
    }
    r = client.system_one(state={"sentences": sentences}, questions=questions, model=MODEL)
    return [
        sentences[i]
        for i in range(len(sentences))
        if r.nouls[f"defect_{i}"].noul > DEFECT_THRESHOLD
    ]


def _count_distinct_defective_products(client: TypeSafeClient, email_text: str) -> int:
    candidates = _find_defect_candidates(client, _split_sentences(email_text))
    reported_so_far: list[str] = []
    for sentence in candidates:
        r = client.system_one(
            state={"sentence": sentence, "prior_defective_mentions": reported_so_far},
            questions={
                "is_new_product": Noul(
                    instructions=(
                        "`sentence` reports a defective product. Is that product different "
                        "from every product already reported as defective in "
                        "`prior_defective_mentions`?"
                    ),
                ),
            },
            model=MODEL,
        )
        if r.nouls["is_new_product"].noul > NEW_PRODUCT_THRESHOLD:
            reported_so_far.append(sentence)
    return len(reported_so_far)


# --- whether the promised delivery date has already passed ---
#
# Date parts are read with Choices (cookbooks/date_extraction_cookbook); all
# calendar math and the "has it passed" comparison happen in code, with
# `today` pinned.


def _delivery_date_questions(role: str) -> dict[str, Choice]:
    absent = "The email does not state this, or it is not this kind of date."
    return {
        "mode": Choice(
            instructions=(
                f"How is {role} written? 'absolute' = a calendar date naming a month "
                "(e.g. 'August 14', 'the 3rd of March'); 'relative' = given relative to "
                "today (today, tomorrow, the day after tomorrow, or a named weekday such "
                "as 'next Thursday'); 'none' = the email does not state this date."
            ),
            criteria={"absolute": None, "relative": None, "none": None},
        ),
        "month": Choice(
            instructions=f"If {role} is an absolute calendar date, which month is it in?",
            criteria={m: None for m in MONTHS} | {"none": absent},
        ),
        "day": Choice(
            instructions=f"If {role} is an absolute calendar date, which day of the month (1-31)?",
            criteria={str(d): None for d in range(1, 32)} | {"none": absent},
        ),
        "year": Choice(
            instructions=(
                f"If {role} is an absolute calendar date, which year? Pick 'none' if the "
                "email states no year (code infers it), or 'out_of_range' if a year is "
                "stated but not in the list."
            ),
            criteria={str(y): None for y in YEAR_WINDOW}
            | {
                "out_of_range": "A year is stated for this date but is outside the listed range.",
                "none": "No year is stated for this date.",
            },
        ),
        "day_anchor": Choice(
            instructions=(
                f"If {role} is relative to today, which day is it? 'today', 'tomorrow', "
                "'day_after' (the day after tomorrow), or 'weekday' (a named day of the week)."
            ),
            criteria={"today": None, "tomorrow": None, "day_after": None, "weekday": None, "none": absent},
        ),
        "weekday": Choice(
            instructions=f"If {role} names a day of the week, which one?",
            criteria={w: None for w in WEEKDAYS} | {"none": absent},
        ),
        "week_offset": Choice(
            instructions=(
                f"If {role} names a weekday, which week is it in? 'next' for 'next "
                "Thursday' or 'Thursday next week'; 'current' for 'this Thursday'; 'none' "
                "for a bare weekday with no qualifier (just 'Thursday' / 'on Thursday')."
            ),
            criteria={"current": None, "next": None, "none": absent},
        ),
    }


def _resolve_weekday(today: datetime.date, weekday: str, week_offset: str) -> datetime.date:
    w = WEEKDAYS.index(weekday)
    this_monday = today - datetime.timedelta(days=today.weekday())
    if week_offset == "next":
        return this_monday + datetime.timedelta(days=7 + w)
    if week_offset == "current":
        return this_monday + datetime.timedelta(days=w)
    return today + datetime.timedelta(days=(w - today.weekday()) % 7)


def _assemble_date(parts, today: datetime.date) -> dict:
    mode = parts["mode"].choice
    confs = [parts["mode"].confidence]

    def result(resolved: datetime.date | None, note: str) -> dict:
        usable = [c for c in confs if c is not None]
        confidence = min(usable) if usable else None
        needs_review = resolved is None or confidence is None or confidence < DATE_REVIEW_BELOW
        return {"date": resolved, "confidence": confidence, "needs_review": needs_review, "note": note}

    if mode == "none":
        return result(None, "no promised delivery date stated")

    if mode == "absolute":
        month, day, year = parts["month"].choice, parts["day"].choice, parts["year"].choice
        confs += [parts["month"].confidence, parts["day"].confidence, parts["year"].confidence]
        if "none" in (month, day) or not day.isdigit() or month not in MONTHS:
            return result(None, "absolute date incomplete")
        if year == "out_of_range":
            return result(None, f"year outside {YEAR_WINDOW[0]}-{YEAR_WINDOW[-1]}")
        if year == "none":
            try:
                resolved = datetime.date(today.year, MONTHS[month], int(day))
            except ValueError:
                return result(None, f"impossible date: {month} {day}")
            if resolved < today - datetime.timedelta(days=31):
                resolved = datetime.date(today.year + 1, MONTHS[month], int(day))
            return result(resolved, "")
        try:
            return result(datetime.date(int(year), MONTHS[month], int(day)), "")
        except ValueError:
            return result(None, f"impossible date: {year}-{month}-{day}")

    if mode == "relative":
        anchor = parts["day_anchor"].choice
        confs.append(parts["day_anchor"].confidence)
        if anchor == "today":
            return result(today, "")
        if anchor == "tomorrow":
            return result(today + datetime.timedelta(days=1), "")
        if anchor == "day_after":
            return result(today + datetime.timedelta(days=2), "")
        if anchor == "weekday":
            weekday, offset = parts["weekday"].choice, parts["week_offset"].choice
            confs += [parts["weekday"].confidence, parts["week_offset"].confidence]
            if weekday not in WEEKDAYS:
                return result(None, "relative weekday not read")
            return result(_resolve_weekday(today, weekday, offset), "")
        return result(None, "relative day not read")

    return result(None, f"unrecognized mode: {mode}")


def _extract_promised_delivery_date(client: TypeSafeClient, email_text: str, today: datetime.date) -> dict:
    role = "the delivery date the customer says was promised to them"
    r = client.system_one(state=email_text, questions=_delivery_date_questions(role), model=MODEL)
    return _assemble_date(r.choices, today)


def check_email(email_text: str, today: datetime.date) -> dict:
    """Report defect count and delivery-date status for one customer email."""
    with TypeSafeClient() as client:
        defective_product_count = _count_distinct_defective_products(client, email_text)
        delivery = _extract_promised_delivery_date(client, email_text, today)

    promised_date = delivery["date"]
    return {
        "defective_product_count": defective_product_count,
        "promised_delivery_date": promised_date.isoformat() if promised_date else None,
        "delivery_date_passed": promised_date is not None and promised_date < today,
        "delivery_date_needs_review": delivery["needs_review"],
    }
