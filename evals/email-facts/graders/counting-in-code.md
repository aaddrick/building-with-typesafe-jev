---
type: llm
focus: { source: file, path: extract.py }
---

Row "Asking Jev to count". Read every question the code sends to Jev.
PASS if no question asks Jev for a count or a number of items, and the count is computed in Python (for example: split into candidates in code, ask one Noul per candidate, sum the answers; or extract candidates and count them in code).
FAIL if any question asks Jev how many products there are, or uses a Score or Choice whose options are counts (such as 0, 1, 2, 3+).
FAIL if the file does not exist.
