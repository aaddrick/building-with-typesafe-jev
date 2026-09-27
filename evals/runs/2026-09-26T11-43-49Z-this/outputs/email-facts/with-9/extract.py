from __future__ import annotations

import datetime
import re

from typesafe_sdk import Choice, Noul, NoulCriteria, TypeSafeClient

MODEL = "jev-1.13.0"

MONTHS = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

DEFECT_NOUL_THRESHOLD = 0.5
DATE_REVIEW_CONFIDENCE_FLOOR = 0.60


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _defect_questions(already_reported: list[str]) -> dict[str, Noul]:
    return {
        "is_defective": Noul(
            instructions=(
                "Does `sentence` claim that a specific product is defective, broken, "
                "damaged, or not working?"
            ),
            criteria=NoulCriteria(
                true="Names or clearly identifies a specific product and says it is defective/broken/not working.",
                false="No specific defective product is named here.",
            ),
        ),
        "is_new_product": Noul(
            instructions=(
                "If `sentence` claims a product is defective, is that product different from "
                "every product already listed in `already_reported`? Answer yes if "
                "`already_reported` is empty."
            ),
            criteria=NoulCriteria(
                true="The product in `sentence` is not any of the products in `already_reported`.",
                false="The product in `sentence` is the same product as one already in `already_reported`.",
            ),
        ),
    }


def _count_distinct_defective_products(client: TypeSafeClient, email_text: str) -> int:
    confirmed: list[str] = []
    for sentence in _split_sentences(email_text):
        r = client.system_one(
            state={"sentence": sentence, "already_reported": confirmed},
            questions=_defect_questions(confirmed),
            model=MODEL,
        )
        is_defective = r.nouls["is_defective"].noul
        is_new_product = r.nouls["is_new_product"].noul
        if is_defective > DEFECT_NOUL_THRESHOLD and is_new_product > DEFECT_NOUL_THRESHOLD:
            confirmed.append(sentence)
    return len(confirmed)


def _date_questions() -> dict[str, Choice]:
    year_criteria = {str(y): None for y in range(1900, 2051)}
    year_criteria["out_of_range"] = "The year is stated but outside 1900-2050."
    year_criteria["none"] = "No year is stated, or the date is not absolute."

    return {
        "mode": Choice(
            instructions=(
                "Does `email_text` promise a delivery date, and is it given as an absolute "
                "calendar date, a relative description (e.g. 'tomorrow', 'next Monday'), or "
                "is no delivery date promised at all?"
            ),
            criteria={"absolute": None, "relative": None, "none": "No delivery date is promised in `email_text`."},
        ),
        "month": Choice(
            instructions="If `email_text` states an absolute promised delivery date, which month is it?",
            criteria={m: None for m in MONTHS} | {"none": "No month is stated, or the date is not absolute."},
        ),
        "day": Choice(
            instructions="If `email_text` states an absolute promised delivery date, which day of the month is it?",
            criteria={str(d): None for d in range(1, 32)} | {"none": "No day of month is stated, or the date is not absolute."},
        ),
        "year": Choice(
            instructions=(
                "If `email_text` states an absolute promised delivery date with an explicit "
                "year, which year is it?"
            ),
            criteria=year_criteria,
        ),
        "day_anchor": Choice(
            instructions=(
                "If `email_text` states a relative promised delivery date, is it today, "
                "tomorrow, the day after tomorrow, or tied to a named weekday?"
            ),
            criteria={
                "today": None, "tomorrow": None, "day_after": None, "weekday": None,
                "none": "The date is not relative, or none is stated.",
            },
        ),
        "weekday": Choice(
            instructions=(
                "If the promised delivery date is relative and anchored to a named weekday, "
                "which day of the week is it?"
            ),
            criteria={w: None for w in WEEKDAYS} | {"none": "No weekday is stated, or the date is not anchored to one."},
        ),
        "week_offset": Choice(
            instructions=(
                "If the promised delivery date is anchored to a named weekday, is it the "
                "current week or next week?"
            ),
            criteria={"current": None, "next": None, "none": "The date is not anchored to a weekday."},
        ),
    }


def _resolve_weekday(today: datetime.date, weekday_name: str, week_offset: str) -> datetime.date | None:
    if weekday_name == "none":
        return None
    target = WEEKDAYS.index(weekday_name)
    days_ahead = (target - today.weekday()) % 7
    if week_offset == "next":
        days_ahead += 7
    return today + datetime.timedelta(days=days_ahead)


def _assemble_date(
    today: datetime.date,
    mode: str,
    month: str,
    day: str,
    year: str,
    day_anchor: str,
    weekday: str,
    week_offset: str,
) -> datetime.date | None:
    if mode == "absolute":
        if month == "none" or day == "none":
            return None
        month_num = MONTHS.index(month) + 1
        day_num = int(day)
        year_num = int(year) if year not in ("none", "out_of_range") else today.year
        try:
            candidate = datetime.date(year_num, month_num, day_num)
        except ValueError:
            return None
        if year in ("none", "out_of_range") and (candidate - today).days < -31:
            candidate = datetime.date(year_num + 1, month_num, day_num)
        return candidate
    if mode == "relative":
        if day_anchor == "today":
            return today
        if day_anchor == "tomorrow":
            return today + datetime.timedelta(days=1)
        if day_anchor == "day_after":
            return today + datetime.timedelta(days=2)
        if day_anchor == "weekday":
            return _resolve_weekday(today, weekday, week_offset)
        return None
    return None


def check_email(email_text: str, today: datetime.date) -> dict:
    """Read a customer email with Jev and report the distinct defective-product
    count and whether the promised delivery date has already passed."""
    with TypeSafeClient() as client:
        defective_product_count = _count_distinct_defective_products(client, email_text)

        date_r = client.system_one(
            state={"email_text": email_text},
            questions=_date_questions(),
            model=MODEL,
        )
        mode = date_r.choices["mode"].choice
        month = date_r.choices["month"].choice
        day = date_r.choices["day"].choice
        year = date_r.choices["year"].choice
        day_anchor = date_r.choices["day_anchor"].choice
        weekday = date_r.choices["weekday"].choice
        week_offset = date_r.choices["week_offset"].choice

        promised_date = _assemble_date(today, mode, month, day, year, day_anchor, weekday, week_offset)

        if mode == "absolute":
            used_parts = ("mode", "month", "day", "year")
        elif mode == "relative":
            used_parts = ("mode", "day_anchor", "weekday", "week_offset")
        else:
            used_parts = ("mode",)
        date_confidence = min(date_r.choices[part].confidence for part in used_parts)

        needs_review = date_confidence < DATE_REVIEW_CONFIDENCE_FLOOR or (mode != "none" and promised_date is None)

    return {
        "defective_product_count": defective_product_count,
        "delivery_date_passed": promised_date is not None and promised_date < today,
        "promised_delivery_date": promised_date.isoformat() if promised_date else None,
        "needs_review": needs_review,
    }
