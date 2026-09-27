# Prior Art Index

Community projects built on Jev, grouped by **implementation shape**, snapshot 2026-09-25 (10 days after launch). Most are weekend projects. Treat them as design references, not proven production systems. Numbers are author-reported.

## How to use

1. Find your intent in the table. Open only that shape file.
2. Or grep: `grep -ril "<keyword>" ~/.claude/skills/building-with-typesafe-jev/prior-art/`. Try a domain word (trading, drone, email, SQL, dubbing) or a mechanism word (beam, cascade, lease, tick).
3. Each shape file has: the shape → a code sketch → field lessons → prior art with links. Fetch a linked repo only when you need its details.

Link conventions: `gh:owner/repo` = `https://github.com/owner/repo`. `HN:<id>` = `https://news.ycombinator.com/item?id=<id>`. Items with no link come from the indexes at the bottom.

## Find the shape

| I want to… | Shape file | Core move |
|---|---|---|
| Act every tick in a game, sim, robot, market, or UI | `control-loops.md` | State → Choice over the legal actions. Code executes. |
| Pick the right thing from a list (UI element, tool, function args, extracted value, model tier) | `select-from-candidates.md` | Candidates become Choice keys. Jev never generates. |
| Allow, block, or require approval before something happens | `gates.md` | Noul/Choice verdict + deterministic policy + escalation |
| Filter or label every item in a big or endless stream (posts, logs, rows, emails) | `stream-filters.md` | One cheap request per item. The threshold lives in code. |
| Sort, rerank, dedupe, match, or walk a graph or taxonomy | `ranking-and-matching.md` | A Noul per pair, or a Choice per level, plus beam search |
| Grade outputs, traces, or content against a rubric | `judges-and-evals.md` | Atomic rubric questions, combined in code |
| Decide on partial input as it arrives (speech, typing, video) | `incremental-realtime.md` | Re-ask on every increment. Commit at a confidence bar. |
| Manage an agent's context, memory, effort, or stopping | `agent-context-memory.md` | Keep/drop/lease/effort decisions instead of summaries |
| Combine Jev with an LLM (planner/actor, cascade, distillation) | `llm-pairing.md` | Jev handles the fast, frequent part. The LLM handles the rare, hard part. |
| Use Jev answers as data (ML features, research measurement, benchmarks) | `research-and-features.md` | Probabilities become columns or measurements |
| Put Jev inside existing infrastructure (SQL, vector DB, CI, middleware, Home Assistant) | `embedding-in-infrastructure.md` | Wrap one call as a native primitive of the host |
| Classify into **more than about 255 options** (catalog, taxonomy, skill roster) | `ranking-and-matching.md` → Walk | A Choice caps at 255. Walk the tree level by level with beam search, or pre-rank then pick. |
| Detect a pattern across a **window or burst of events** (raid, fraud burst, incident, alert storm), then act | `gates.md` (+ `stream-filters.md` for per-event labels) | Code computes the window stats (rates, counts, ages) and samples a few events into the state. Jev judges the pattern. A gate policy decides the action. |

**Many designs combine two shapes.** Open the one that owns the final decision first (usually a gate or a control loop), then the one that feeds it.

## Known bad fits (the field tried these and failed)

- **Chess, and puzzle-like search**: it blunders on every move (HN:49746967). Keep search in code.
- **Code review as the only reviewer**: too weak at reasoning (HN:49842208). Triage and risk scoring work. Final judgment does not.
- **Perception**: Jev is text-only. Self-driving pushback: perception is the bottleneck (HN:49722214). Do perception with CV first.
- **NSFW image flagging via an open "VisionLaya" clone**: too many false positives (HN:49779502).
- **Record dedupe and a personal prompt router**: one user found these "underwhelming / OK at best" (HN:49842510).
- **Out-of-box calibration claims**: a fair die gave face 1 about 83%. Fit Platt scaling on your own labels (HN:49830385, HN:49839995).
- **Speed marketing**: measured gains were about 5–7× over small LLMs, not 40–200× (HN:49845146). Batched LLM calls can match it offline.

## Bigger indexes (for more than these files hold)

- https://github.com/valentynkit/awesome-jev-typesafe (about 250 entries)
- https://www.jevdirectory.org/resources (about 515)
- https://github.com/walidboulanouar/awesome-jev-use-cases (X demos)
- https://github.com/AbdelStark/awesome-typesafe-jev
- https://docs.typesafe.ai/concepts/use-case-map.md (official, by industry)
- https://evals.typesafe.ai/ (official eval workflows: invoice, SOC, support)
