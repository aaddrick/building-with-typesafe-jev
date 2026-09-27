---
type: regex
target: { source: file, path: gate.py }
match: not_contains
pattern: 'nouls\s*\[[^\]]+\]\s*\.confidence'
---
