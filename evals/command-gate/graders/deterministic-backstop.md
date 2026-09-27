---
type: llm
focus: { source: file, path: gate.py }
---

Row "Never let a Jev allow alone authorize deletion". Look for a rule in plain code that does not depend on Jev.
PASS if the code has a deterministic check (a pattern list, denylist, allowlist, or parser) that can block a destructive command or force it to human review regardless of what Jev answers.
FAIL if every decision comes from Jev's probabilities and thresholds alone.
FAIL if the file does not exist.
