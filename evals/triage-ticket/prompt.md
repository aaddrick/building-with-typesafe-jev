---
description: The README's "What changes" comparison. One triage task, same prompt in both arms; the only difference is whether the plugin is loaded.
tags: [readme-claims]
plugins: ["../.."]
runs: 3
max_turns: 80
timeout_seconds: 1500
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite]
---

Write a support-ticket triage function in Python that uses typesafe.ai's Jev model (the System One API). Given a ticket's text, it should decide which department handles it, how severe the problem is, and whether the customer is asking for a refund, then return a routing decision. When the function is not sure enough of the department, the decision should send the ticket to a person instead. When a ticket could belong to a second department, name that one too. Along with the severity, report how likely it is that the problem is at the most severe level. The function will run on a busy queue, so it has to cope with rate limits. Put the function in `triage.py` in the current directory.

Jev's docs are at https://docs.typesafe.ai.
