---
type: regex
target: { source: file, path: label_logs.py }
match: not_contains
pattern: 'time\.sleep|asyncio\.sleep|for\s+\w*attempt|(?:^|\n)[ \t]*while\s[^\n]*retr'
flags: i
---
