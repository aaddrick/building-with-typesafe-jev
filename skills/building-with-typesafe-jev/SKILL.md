---
name: building-with-typesafe-jev
description: Use when code needs a judgment about natural language that rules or regex cannot make (classify, route, triage, moderate, score, rank, match, dedupe, filter, extract, verify, or gate an action), when brainstorming where AI could fit in an app, when an LLM call exists only to pick a label, score, or yes/no, or when code uses TypeSafe AI, Jev, System One, typesafe-sdk, or @typesafe-ai/sdk.
---

# Building with TypeSafe Jev

## Overview

Jev is a **System One model**: it takes a `state` plus named, typed questions and returns typed answers with calibrated probabilities. It never generates text. **Code owns the workflow. Jev supplies narrow snap judgments.** It is not a chat or coding LLM and cannot power a coding agent.

**Before you design anything new, check prior art:** open `prior-art/INDEX.md`. It maps intents (control loop, gate, rerank, stream filter, incremental, agent memory, LLM pairing, and more) to shape files. Each shape file has a code sketch, field lessons, and linked community projects. Or grep `prior-art/` for a domain word. It also lists the known bad fits.

Exact request/response shapes, SDK signatures, limits, and errors: see `api-reference.md`. It ends with a map of which live docs page to read for which task. Patterns and the cookbook index: see `patterns.md`. The live docs win on conflict: fetch `https://docs.typesafe.ai/llms.txt`, and append `.md` to any page path. Do not guess field names. Check them there. If the docs cannot be reached, read the installed SDK's types, tell the user you did, and do not invent details that depend on the version.

**Open-ended request** ("where could AI help in this app?"): work backward from what the app should show, select, change, or hand off. Offer two or three directions from `prior-art/INDEX.md` and recommend one. **Concrete request:** pick the shape and build. Either way, keep the user's stack and scope, and add Jev only where code needs a judgment.

## Test against the live API when you can

You get better results when you check a design against the real endpoint. A live call catches a wrong field name, and it shows when Jev reads a question differently than you meant. If `TYPESAFE_API_KEY` is set in your shell, run a small probe before the code reaches the project. One call costs a fraction of a cent (input tokens only, 4.2 cents per million). If the key is not set, design from `api-reference.md` and say that you did. Do not go looking for the key in `.env` files, shell profiles, or key files. Point the user to the README section "If the agent cannot see the key".

**Rules for the key:**
- Do not print, echo, log, or commit it.
- Do not hardcode it or pass `api_key=` in code. Let the SDK read `TYPESAFE_API_KEY`. Keep it server-side.
- `TYPESAFE_LOG_LEVEL=debug` logs request bodies without redaction. Headers stay redacted.
- A `401` or `TypeSafeAuthenticationError` means the key is wrong or rotated. Ask the user to replace it where they stored it, never in the chat.
- Keep a task to about 10 test calls, and probe loops to about 8 workers or fewer. Rate limits are shared across the account.

## Pick the primitive

| Answer shape | Primitive | Returns | Branch on |
|---|---|---|---|
| One of an unordered set | `Choice` (≤255 options, map) | `choice`, `probabilities`, `confidence` | `choice`; gate with `confidence` |
| Position on a spectrum you can describe | `Score` (2–10 levels, ordered list) | `score` (0…n-1, can be fractional), `legend`, `probabilities`, `confidence` | threshold or sort `score` |
| Yes/no | `Noul` (optional `true`/`false` criteria) | `noul` = P(yes), **no `confidence`** | `noul > threshold` |

A Noul of 0.5 means "unsure", never "medium". Degree questions ("how strong in Python") need a Score. Several labels that can apply at once need one Noul per label, not a Choice.

## Rules

1. **One snap judgment per question.** Pose something a knowledgeable person decides in a second. Split "angry AND wants refund" into two questions and combine them in code. Atomic does not mean trivial: picking one bounded action or reading one message in context is a single judgment. Do not split apart a relationship the question is about (does this passage support that claim?).
2. **Put every question for one state in one request**, including speculative ones. They run in parallel and in isolation. Extra questions add almost no latency, but each one adds input tokens, so check `usage.input_tokens` on a real request. Write the premise into the text: `"If this is a technical problem, how severe is it?"`. Code ignores the answers on branches it does not take.
3. **A second request only when the first answer is needed to build it**: to fetch more state, to build new state, or to pick the next options (hierarchical walk, shortlist then full text).
4. **Question IDs are never sent to the model.** Write the full question in `instructions`.
5. **Write the exact condition.** Jev reads literally: it answers the question you wrote, not the one you meant. Scope words, negations, and implied conditions count at face value. When a wrong answer makes you explain what you really meant, that explanation is the missing half of the instruction. Put boundary cases in the criteria. Avoid double negatives and property-of-a-property hops. Name the state path instead.
6. **Structure state as a named JSON object.** Point at parts with backticked paths: ``"Does `ticket.messages[0].text` request a refund?"``. Send only what the question needs. Irrelevant state lowers accuracy. Include metadata (plan, timestamps) only when a question refers to it.
7. **Score levels describe situations, not degrees.** Write `"Broken feature, workaround exists"`, not `"moderate"` or `"2"`. Each level is judged alone, so "worse than the previous level" means nothing. Give each level one dimension.
8. **Choice: give the full option list plus `other` / `none_of_the_above`**. When two options get confused, make each value an object: `{"what": ..., "not_for": ..., "examples": [...]}`. Use the same keys on every option.
9. **Phrase a Noul so that high = yes.** Keep criteria aligned with the instruction. Never map `true` to a "no" meaning.
10. **Keep math, counting, dates, and exact lookups in code.** To count, ask one Noul per candidate and sum. For dates, extract the parts with Choices (include `not_stated`) and compare in code. For extraction, find candidates with regex or an LLM, then let Jev pick among them. To count distinct items, split into candidates in code (sentences, lines). Ask two Nouls per candidate: "is this an X?" and "is this X different from those in `items[0..i-1]`?". Sum the answers in code. Turn hex colors, RGB triples, and raw codes into a computed number or a named bucket before Jev sees them. The same goes for a safety condition you can write exactly, when a miss cannot be undone: a denylist of destructive commands, a spending limit, a protected branch. Check it in code before Jev runs. Jev may make that decision stricter, never looser.
11. **Put questions, thresholds, and weights in one constants module.** Those are what humans review and tune.

## Using the numbers

- **Only picking the best option?** Use `choice` (the argmax). A confidence threshold is not needed.
- **Acting on it?** Split into three bands: act / confirm or review / escalate to a human or a reasoning LLM. Scale each threshold to what a wrong action costs. A read-only action can take a lower bar than a money-moving one.
- **Escalate only on uncertainty that feeds an action.** Report uncertainty on informational outputs, and ignore it on branches the code does not take.
- **Belongs to two categories?** Route to `choice`, and notify a second option whose probability is above about 0.25. Do not force a single label.
- **Confidence of 1.0 is normal** when all the probability sits on one option. It is not a bug.
- **Composite judgment?** Normalize each Score with `score / (len(criteria) - 1)`, weight the results in code, and keep the raw answers.
- **A fractional `score` works for thresholds and sorting only.** Do not read an exact magnitude off it by interpolating between two levels.
- **A Choice always has a winner**, even when nothing fits. Add an absolute Noul (`exists`, `stated`, `fits`) in the same request to decide whether to act at all.
- **Combine parts with the minimum** (a date from its parts, a call from its arguments). **Combine "something is wrong" flags with the maximum**, not the average.
- **Confidence is not the top probability.** For a Choice it is `(n·top − 1)/(n − 1)` over n options (measured: top 0.92 of 3, confidence 0.88), so it depends only on the top probability and the option count. Score confidence also counts how far the rest of the probability sits from the top level: spread onto a neighboring level costs little, and mass at the far end costs a lot. See `api-reference.md`. Neither is proof of correctness: typed output guarantees the interface, not the truth. Tune thresholds on labeled data from the user, and plot confidence against accuracy to check them. Treat cookbook numbers as examples only.
- **Every number comes back rounded to 0.01.** Nouls, probabilities, and confidence tie often. Give any sort on them a tiebreaker.
- Do not carry a threshold from a Noul to a Choice. Do not expect `P(q) + P(not q) = 1` across separate questions.
- Pin `jev-1.13.0` when thresholds were tuned against it. Log `response.model`.

## When an answer is wrong

Look at the exact state, questions, candidates, answers, and the code that combined them, next to what actually happened. Then name the cause before you change anything:

- **Missing evidence**: the state lacked what the question needed, or a candidate was never offered.
- **Model error**: the state held the answer. Rewrite the question (rule 5) and re-test on the same case, or route cases like it to review.
- **Code error**: wrong path, inverted Noul, bad threshold, or wrong combination.
- **Service failure**: a timeout, a 429, or a 5xx. Handle it with the SDK's `RetryPolicy`, not by rewording the question.

Known weak spots in jev-1.13: `https://docs.typesafe.ai/model-jaggedness/jev-1.13.md`.

## Common mistakes

| Mistake | Fix |
|---|---|
| One API call per question | Put all questions in one `system_one` call |
| Treating the top probability as confidence | Use `.confidence`. It is computed for you and is never higher than the top probability. |
| Guessing the `score` scale | It is 0 to n-1, weighted by level probability. Python keys `legend`/`probabilities` by int; HTTP keys them by string. |
| `Score.criteria` as a dict keyed by int | Use an ordered list (SDK ≥ 0.6.0) |
| Numeric or vague Score levels | Use concrete situations, one dimension each |
| "Analyze this and decide what to do" | Split into atomic questions and combine in code |
| Asking Jev to count, do date math, or compare hex colors | Do it in code. Ask per-item Nouls. |
| Double negatives, or "does the thing it refers to have..." | Ask directly about a named state path |
| Speculative question with no stated premise | `"If X, then ...?"` |
| Hand-rolled 429 retry loop | The SDKs retry 429/5xx with backoff. Tune with `RetryPolicy`. |
| 16+ worker thread pool on one key | Use about 8 workers or fewer. Above that, the endpoint rate-limits. |
| Holistic "is this record good?" judge | Use per-field checks, one flaw per Noul |
| API key in browser code | Keep it server-side. JS needs `dangerouslyAllowBrowser` for a reason. |
| Jev as the only check before a destructive or money-moving action | Put a code rule first: a known-bad pattern blocks whatever Jev says. Jev judges only what the rule does not decide. |
| Hostile text in state | Jev does not treat state as adversarial. Keep untrusted text in its own named field. Point questions at it by path. Add an injection Noul. Never let a Jev answer alone authorize a side effect. |
