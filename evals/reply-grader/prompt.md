---
description: Judge shape. A 1-10 grade tempts one holistic question with numeric levels.
tags: [judges]
plugins: ["../.."]
runs: 3
max_turns: 80
timeout_seconds: 1500
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite]
---

Write `grade.py` with a function `grade(customer_message: str, agent_reply: str) -> dict` that uses typesafe.ai's Jev model to grade a support agent's reply on a 1-10 scale against our rubric: the reply is consistent with what the customer said, it is polite, it actually resolves the issue, and it does not promise a refund (only billing may promise refunds). Return the score and the list of problems found.

Jev's docs are at https://docs.typesafe.ai.
