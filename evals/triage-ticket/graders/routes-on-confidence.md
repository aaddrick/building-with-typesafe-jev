---
type: regex
target: { source: file, path: triage.py }
pattern: 'confidence\b[^\n]{0,40}[<>]|[<>]=?\s*[\w.\[\]"'']*confidence'
flags: i
---
