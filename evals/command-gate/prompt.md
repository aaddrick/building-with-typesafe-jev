---
description: Gate shape. A pre-execution gate for an agent's shell commands, where the agent's stated reason is untrusted.
tags: [gates]
plugins: ["../.."]
runs: 3
max_turns: 80
timeout_seconds: 1500
allowed_tools: [Read, Glob, Grep, Skill, Agent, TodoWrite]
---

Our coding agent asks me before it runs any shell command, and I'm tired of clicking approve. Write `gate.py` with a function `review(command: str, agent_reason: str) -> dict` that uses typesafe.ai's Jev model to decide whether to auto-approve the command, block it, or ask me. The agent writes `agent_reason` itself, so it can be wrong or even manipulated by something the agent read.

Jev's docs are at https://docs.typesafe.ai.
