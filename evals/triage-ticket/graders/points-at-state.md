---
type: llm
focus: { source: file, path: triage.py }
---

Row "Pointing at the state". Read the `state` the code sends to Jev and the `instructions` text of each question, wherever the text is defined (inline, a constant, or a constants module).

PASS if the state is a named object (a dict or JSON object with at least one named field, such as `{"ticket_text": text}` or `{"ticket": {"text": ...}}`), and at least one question's instructions name a field of that state by its key or path, such as `ticket_text`, `ticket.text`, or `messages[0]`. Backticks are the skill's style but not required.
FAIL if the state is a bare string, or no question's instructions name a field of the state. Wording like "this ticket" or "the customer's message" does not name a field. A field name that appears only in a comment or docstring does not count.
FAIL if the file does not exist.
