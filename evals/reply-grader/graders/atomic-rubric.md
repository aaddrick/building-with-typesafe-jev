---
type: llm
focus: { source: file, path: grade.py }
---

Row "Holistic judge". Read the questions sent to Jev.
PASS if each rubric criterion is its own question (or its own set of questions) and the 1-10 grade is computed in Python from those answers.
FAIL if a single question asks Jev for the overall 1-10 grade or for "how good is this reply" as a whole.
FAIL if the file does not exist.
