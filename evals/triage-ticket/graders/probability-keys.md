---
type: regex
target: { source: file, path: triage.py }
match: not_contains
pattern: 'probabilities\s*(\.get\(\s*|\[\s*)(str\(|f["'']|["'']\d)'
---
