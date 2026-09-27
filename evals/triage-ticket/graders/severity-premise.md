---
type: llm
focus: { source: file, path: triage.py }
---

Row "Premise". Read the text of the severity question and its levels.

PASS if the severity question states its premise in its own text (for example "If this is a technical problem, how severe is it?"), or if the question and its levels apply to every ticket, including a ticket that reports no problem at all (for example a level for "a question; nothing is broken").
FAIL if the question asks how severe a problem is while presupposing that a problem exists, and no level fits a ticket that reports no problem.
FAIL if the file does not exist.
