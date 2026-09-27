---
description: Rule 10. Counting and date comparison must stay in code, not in a Jev question.
tags: [rules]
plugins: ["../.."]
runs: 3
max_turns: 80
timeout_seconds: 1500
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite]
---

Write `extract.py` with a function `check_email(email_text: str, today: datetime.date) -> dict` that uses typesafe.ai's Jev model to read a customer email and report two things: how many different products the customer says are defective, and whether the delivery date they were promised has already passed.

Jev's docs are at https://docs.typesafe.ai.
