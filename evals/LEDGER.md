# Eval ledger

One row per kept eval batch. An eval batch is the three arms started together
by `EVAL_PLUGIN=all`, kept as `runs/<batch>-none`, `runs/<batch>-this`, and
`runs/<batch>-official`. Compare scores only within a row, and only between
rows whose case files, models, and run counts match.

Commit is the repo state the eval batch used, from its `provenance.json`.
"Pre-flatten" marks a commit from before the history was squashed into one
commit, so it cannot be checked out. A `+`
means files that shape a run (under `skills/`, `.claude-plugin/`, or `evals/`
other than this ledger, `README.md`, `docs/`, and `runs/`) had uncommitted
changes; the notes list them. Judges lists the in-run judge first, then the
ones `rejudge.py` added; llm checks take the majority of them. Scores are the
mean over all cases, and the two difference columns are this plugin minus the
other arm, all with the 95% range from `compare.py`.

| Eval batch | Commit | Official ref | Agent | Judges | Claude Code | Runs/arm | No plugin | This plugin | Official | This vs no plugin | This vs official | Cost | Notes |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| [2026-09-26T11-43-49Z](runs/) ([none](runs/2026-09-26T11-43-49Z-none/), [this](runs/2026-09-26T11-43-49Z-this/), [official](runs/2026-09-26T11-43-49Z-official/)) | 85a88f9 (pre-flatten) | 65a39f3 | claude-sonnet-5 | claude-opus-5-5, gpt-6-sol, kimi-k3 | 2.1.283 | 10 | 0.65 ± 0.05 | 0.96 ± 0.02 | 0.77 ± 0.04 | +0.30 ± 0.05 | +0.19 ± 0.04 | $92.27 | First baseline on the keyless three-container harness. This plugin 0.2.0, official 0.5.7; runs $26.88 none, $23.95 this, $31.88 official; re-judge $3.42 gpt-6-sol, $6.14 kimi-k3. The panel overturns 4 of Opus's 390 llm verdicts; with Opus alone the no-plugin score is 0.66 ± 0.04. Judges split on `untrusted-reason-isolated` (no plugin: Opus 5, GPT-6 Sol 5, Kimi 9 of 10). `record_finish` crashed after scoring in every arm on a `permission_denied` trace event whose message is a string, so `provenance.json` was written, and the trace scrub finished, on the host by the fixed script; no secret was found in the 180 kept traces. Some runs in both plugin arms tried to use the plugin's `evals/` directory as their project (this: 10 calls in 7 runs; official: 3 in 3), and every call was denied. One no-plugin run loaded Claude Code's bundled `claude-api` skill. `no-hand-rolled-retry` wrongly failed no-plugin `triage-ticket` run 4 on "while" in an error message; with the fixed pattern that case scores 0.45, not 0.44, and no mean moves. After this batch, `triage-ticket`'s prompt gained a fallback for uncertain tickets, so its scores do not compare with later batches. |
