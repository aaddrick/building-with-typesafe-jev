from datetime import date, timedelta

from typesafe_sdk import Choice, Score, TypeSafeClient

REVIEW_BELOW = 0.60

MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}
WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
YEAR_WINDOW = list(range(1900, 2051))

client = TypeSafeClient()


def _questions() -> dict:
    absent = "The document does not state this, or it is not this kind of date."
    role = "the delivery date promised to the customer for their order"
    return {
        "defect_count": Score(
            instructions=(
                "How many different products does the customer describe as defective, "
                "broken, faulty, or otherwise not working? Count each distinct product "
                "once even if it is mentioned more than once."
            ),
            criteria=[
                "No product is described as defective.",
                "Exactly one distinct product is described as defective.",
                "Exactly two distinct products are described as defective.",
                "Exactly three distinct products are described as defective.",
                "Exactly four distinct products are described as defective.",
                "Five or more distinct products are described as defective.",
            ],
        ),
        "mode": Choice(
            instructions=(
                f"How is {role} written, if at all? 'absolute' = a calendar date naming "
                "a month (e.g. 'August 14', 'the 3rd of March'); 'relative' = given "
                "relative to today (today, tomorrow, the day after tomorrow, or a named "
                "weekday such as 'next Thursday'); 'none' = the document does not state "
                "this date."
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
                "document states no year (code infers it), or 'out_of_range' if a year is "
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
            criteria={
                "today": None,
                "tomorrow": None,
                "day_after": None,
                "weekday": None,
                "none": absent,
            },
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


def _resolve_weekday(today: date, weekday: str, week_offset: str) -> date:
    w = WEEKDAYS.index(weekday)
    this_monday = today - timedelta(days=today.weekday())
    if week_offset == "next":
        return this_monday + timedelta(days=7 + w)
    if week_offset == "current":
        return this_monday + timedelta(days=w)
    return today + timedelta(days=(w - today.weekday()) % 7)


def _assemble_date(parts: dict, today: date) -> dict:
    mode = parts["mode"].choice
    confs = [parts["mode"].confidence]

    def result(resolved, note):
        usable = [c for c in confs if c is not None]
        confidence = min(usable) if usable else None
        needs_review = resolved is None or confidence is None or confidence < REVIEW_BELOW
        return {"date": resolved, "confidence": confidence, "needs_review": needs_review, "note": note}

    if mode == "none":
        return result(None, "no delivery date stated")

    if mode == "absolute":
        month, day, year = parts["month"].choice, parts["day"].choice, parts["year"].choice
        confs += [parts["month"].confidence, parts["day"].confidence, parts["year"].confidence]
        if "none" in (month, day) or not day.isdigit() or month not in MONTHS:
            return result(None, "absolute date incomplete")
        if year == "out_of_range":
            return result(None, f"year outside {YEAR_WINDOW[0]}-{YEAR_WINDOW[-1]}")
        if year == "none":
            try:
                resolved = date(today.year, MONTHS[month], int(day))
            except ValueError:
                return result(None, f"impossible date: {month} {day}")
            if resolved < today - timedelta(days=31):
                resolved = date(today.year + 1, MONTHS[month], int(day))
            return result(resolved, "")
        try:
            return result(date(int(year), MONTHS[month], int(day)), "")
        except ValueError:
            return result(None, f"impossible date: {year}-{month}-{day}")

    if mode == "relative":
        anchor = parts["day_anchor"].choice
        confs.append(parts["day_anchor"].confidence)
        if anchor == "today":
            return result(today, "")
        if anchor == "tomorrow":
            return result(today + timedelta(days=1), "")
        if anchor == "day_after":
            return result(today + timedelta(days=2), "")
        if anchor == "weekday":
            weekday, offset = parts["weekday"].choice, parts["week_offset"].choice
            confs += [parts["weekday"].confidence, parts["week_offset"].confidence]
            if weekday not in WEEKDAYS:
                return result(None, "relative weekday not read")
            return result(_resolve_weekday(today, weekday, offset), "")
        return result(None, "relative day not read")

    return result(None, f"unrecognized mode: {mode}")


def check_email(email_text: str, today: date) -> dict:
    """Read a customer email with Jev and report defect count and delivery-date status."""
    answers = client.system_one(state=email_text, questions=_questions()).answers

    defect_count = round(answers["defect_count"].score)
    defect_count_confidence = answers["defect_count"].confidence

    date_parts = {k: v for k, v in answers.items() if k != "defect_count"}
    resolved = _assemble_date(date_parts, today)

    delivery_date = resolved["date"]
    delivery_date_passed = delivery_date < today if delivery_date is not None else None

    return {
        "defective_product_count": defect_count,
        "defective_product_count_confidence": defect_count_confidence,
        "promised_delivery_date": delivery_date,
        "delivery_date_passed": delivery_date_passed,
        "delivery_date_confidence": resolved["confidence"],
        "needs_review": (
            defect_count_confidence is None
            or defect_count_confidence < REVIEW_BELOW
            or resolved["needs_review"]
        ),
        "note": resolved["note"],
    }
