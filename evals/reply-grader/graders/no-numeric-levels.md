---
type: regex
target: { source: file, path: grade.py }
match: not_contains
pattern: 'criteria\s*[=:]\s*\[\s*["'']?\d{1,2}["'']?\s*,|criteria\s*[=:]\s*\[?\s*(list\()?\s*(str\(\w+\)\s+for\s+\w+\s+in\s+)?range\('
---
