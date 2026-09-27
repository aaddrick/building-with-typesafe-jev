---
type: llm
focus: { source: file, path: gate.py }
---

PASS if the function has three outcomes (approve, block, ask the human) and routes uncertain cases, such as a probability in a middle band, to the human.
FAIL if it has only two outcomes, or if uncertain cases are approved or blocked automatically.
FAIL if the file does not exist.
