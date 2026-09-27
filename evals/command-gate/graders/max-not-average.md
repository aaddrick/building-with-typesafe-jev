---
type: regex
target: { source: file, path: gate.py }
match: not_contains
pattern: 'statistics\.mean|np\.mean|fmean\(|sum\([^)]*\)\s*/\s*len\('
---
