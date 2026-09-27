---
type: llm
focus: { source: file, path: extract.py }
---

Row "Asking Jev to do date math". Read every question the code sends to Jev.
PASS if no question asks Jev whether a date has passed, is before or after another date, or how long ago something was, and the comparison with `today` happens in Python with date objects.
FAIL if any question asks Jev to compare the promised date with today or with another date, including by putting today's date into the state and asking whether the date has passed.
FAIL if the file does not exist.
