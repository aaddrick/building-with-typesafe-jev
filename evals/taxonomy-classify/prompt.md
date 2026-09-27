---
description: Walk shape. More than 255 leaf categories, so one Choice cannot hold them.
tags: [ranking]
plugins: ["../.."]
runs: 3
max_turns: 80
timeout_seconds: 1500
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite]
---

`taxonomy.json` in this directory is our product category tree: 12 top-level categories, each with 10 subcategories, each with 10 leaf categories. Write `classify.py` with a function `classify(title: str, description: str) -> str` that uses typesafe.ai's Jev model to return the path of the best leaf category, like `"Home > Kitchen > Knives"`.

Jev's docs are at https://docs.typesafe.ai.
