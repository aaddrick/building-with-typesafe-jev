---
type: llm
focus: { source: file, path: grade.py }
---

Rule "Phrase a Noul so that high = yes". Find the question about refunds.
PASS if there is a question whose yes answer means the reply promises a refund (the bad thing), and the code treats a high probability as a problem.
FAIL if there is no refund question, or if it is phrased so that yes means the reply is fine and the code inverts it.
FAIL if the file does not exist.
