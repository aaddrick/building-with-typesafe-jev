---
type: llm
focus: { source: file, path: triage.py }
---

Row "Score scale". Look at how the code uses the answer to the severity Score question.

PASS if the code uses the `score` value the API returns as the position on the scale (0 to n-1, possibly fractional) for its thresholds or its mapping to levels.
FAIL if the code computes its own position or level from the probabilities instead (for example an expected value, or an argmax over the probabilities in place of `score`), or assumes a different range such as 0 to 1 or 1 to n.
FAIL if the file does not exist or has no Score question.
