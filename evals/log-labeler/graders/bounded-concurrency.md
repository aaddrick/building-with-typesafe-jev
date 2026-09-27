---
type: regex
target: { source: file, path: label_logs.py }
match: not_contains
pattern: '(max_workers|workers|concurrency|Semaphore)\w*\s*[=(:,]\s*(9|[1-9]\d+)\b'
flags: i
---
