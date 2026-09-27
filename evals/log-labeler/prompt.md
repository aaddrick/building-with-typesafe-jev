---
description: Stream-filter shape. Bulk labelling under time pressure on one shared key.
tags: [stream]
plugins: ["../.."]
runs: 3
max_turns: 80
timeout_seconds: 1500
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite]
---

We have a 50,000-line application log. Write `label_logs.py` that reads a log file (one entry per line) and uses typesafe.ai's Jev model to flag the lines that need an on-call engineer, then writes the flagged lines to `flagged.txt`. It needs to get through the whole file quickly.

Jev's docs are at https://docs.typesafe.ai.
