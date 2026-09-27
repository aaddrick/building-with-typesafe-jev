---
type: regex
target: { source: file, path: triage.py }
pattern: 'model\w*\s*[:=]\s*["'']jev-\d+\.\d+\.\d+["'']|\w\.model\b(?!\s*=[^=])|\[\s*["'']model["'']\s*\](?!\s*=[^=])|\.get\(\s*["'']model["'']'
flags: i
---
