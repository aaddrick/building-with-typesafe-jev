---
type: llm
focus: { source: file, path: label_logs.py }
---

Row "Client lifecycle". Look at where the Jev client is created.
PASS if one client (or one per worker thread at most) is created once and reused for every line.
FAIL if the code creates a new client, or opens a new HTTP session, for each line or each request.
FAIL if the file does not exist.
