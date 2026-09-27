# Shape: Judges and Evals

**Use when** you need to grade model outputs, agent traces, content, notes, or submissions against a rubric, online or offline.

## The shape

```
artifact (+ reference, policy) → atomic rubric questions (one flaw or dimension each)
                               → code: max over failure flags, weighted sum over quality dimensions
                               → gold-label test set that measures agreement; diff what flips when questions change
```

```python
from typesafe_sdk import Choice, Noul, Score

TRACE_RUBRIC = {
    "needs_review": Noul(instructions="Should a human review the agent run in `trace`?"),
    "user_disagrees": Noul(instructions="Does the user reject or correct the assistant in `trace.messages`?"),
    "failure_mode": Choice(
        instructions="What is the main way the agent in `trace` fell short?",
        criteria={"wrong_tool": None, "hallucinated_fact": None, "ignored_instruction": None,
                  "gave_up": None, "none": "The run achieved the user's goal"},
    ),
    "severity": Score(
        instructions="If the run in `trace` went wrong, how much harm did it cause the user?",
        criteria=["No harm", "Wasted time, recoverable", "Wrong action taken or data lost"],
    ),
}
```

## Field lessons

- Per-field or per-flaw judges beat one holistic judge ("is this good?" gave 0.56 where per-field checks gave 0.95 and 0.85).
- Treat the questions like code: YAML or constants, versioned, with a gold set and an agreement metric. Before shipping a wording change, diff which rows flip.
- Measured: 85.9% agreement with a frontier judge at 13.6× the speed and 2.7× less cost (Tessl). On the AITA benchmark Jev came 2nd of 7, but only 6.3× faster than Sonnet 5.
- Jev as a judge for code review is weak. Use it to triage and prioritize (P0/P1/P2), not as the final verdict.
- Offline evals: pin the model version, because the `jev-latest` alias moves.

## Prior art

**Platforms**
- Langfuse built-in Jev-as-a-judge evaluators on production traces: [langfuse.com](https://langfuse.com/changelog/2026-09-22-jev-as-a-judge), [langfuse.com](https://langfuse.com/blog/2026-09-18-using-typesafes-jev-for-evals)
- TypeSafe official eval workflows (agent trace QA, support, invoice, SOC): [evals.typesafe.ai](https://evals.typesafe.ai/)
- deepeval Jev metric, harbor rewardkit judges, vercel/ai evaluate, Arize/Opik tracing (in OSS; found by code search)
- "sel-jev-rubric-judge", about 9.2B tokens on OpenRouter: [openrouter.ai](https://openrouter.ai/typesafe/jev-1.13)

**Tools for managing judgments**
- hunch, "dbt for judgments": YAML specs, cached runs, gold-label tests, and a diff of rows that would flip: [oneryalcin/hunch](https://github.com/oneryalcin/hunch)
- jev-align, active labelling + GEPA optimization (sutro-sh)
- JevEval "Jev-as-a-judge": [HN](https://news.ycombinator.com/item?id=49807852)

**Reported judge results**
- Tessl verifiers, 2,725 tests, 85.9% agreement: [HN](https://news.ycombinator.com/item?id=49821631)
- AITA benchmark, 2nd of 7: [HN](https://news.ycombinator.com/item?id=49821894)
- Every's editorial vibe check (X, @danshipper)
- Second-opinion verification of other models' outputs (Good Start Labs): [HN](https://news.ycombinator.com/item?id=49718890)

**Rubric scoring of content**
- Study notes (Knowledge Signal): [HN](https://news.ycombinator.com/item?id=49840561)
- Sentence-by-sentence debate scoring for about $0.05 per video: jevmeter (MarkTechPost launch article)
- Startup idea KILL/FIX/SHIP: killmyidea (awesome-jev-typesafe)
- Persona testing, posts judged by 100–10,000 simulated personas: Crowdcheck (JevDirectory)
- Self-consistency cookbooks (measuring judge stability): [docs.typesafe.ai](https://docs.typesafe.ai/cookbooks/consistency_noul_cookbook.md)

**Code review as triage**
- diffjury: [raihankhan-rk/diffjury](https://github.com/raihankhan-rk/diffjury). jev-review (staged Noul risk matrix): [devagrawal09/jev-review](https://github.com/devagrawal09/jev-review)
- Calibrating Jev as a reviewer: [HN](https://news.ycombinator.com/item?id=49803758). Pushback: [HN](https://news.ycombinator.com/item?id=49842208)
- Semantic linting against AGENTS.md: Perch [HN](https://news.ycombinator.com/item?id=49840204), adhere [HN](https://news.ycombinator.com/item?id=49843708), slop-linter (almcc), taste-lint (npm)
