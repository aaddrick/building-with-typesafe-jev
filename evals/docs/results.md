# Baseline results

The eval batch behind every number in the READMEs. An eval batch is one launch
of `EVAL_PLUGIN=all`: every task, every arm, started together.
[LEDGER.md](../LEDGER.md) lists all kept eval batches.

| | |
|---|---|
| Eval batch | `2026-09-26T11-43-49Z` |
| Commit | `85a88f9`, pre-flatten (see the ledger) |
| Agent | `claude-sonnet-5` |
| Judges | `claude-opus-5-5` in the run; `gpt-6-sol` and `kimi-k3` after; majority of three |
| Claude Code | 2.1.283 |
| Plugins | This plugin 0.2.0; official 0.5.7 at `65a39f3` |
| Raw data | [`runs/2026-09-26T11-43-49Z-*`](../runs/) |

## What the baseline ran

Every task ran 10 times in each of 3 arms: no plugin, this plugin, and the
official plugin. Each run is one `claude -p` session for the agent. Each check
that needs judgment then goes to 3 judges, and each judge votes 3 times, one
call per vote. Pattern-match checks need no model call.

| Task | Agent sessions | Checks (judged) | Check results | Judge calls |
|---|---:|---:|---:|---:|
| `command-gate` | 30 | 6 (3) | 180 | 810 |
| `email-facts` | 30 | 3 (2) | 90 | 540 |
| `log-labeler` | 30 | 3 (1) | 90 | 270 |
| `reply-grader` | 30 | 3 (2) | 90 | 540 |
| `taxonomy-classify` | 30 | 2 (2) | 60 | 540 |
| `triage-ticket` | 30 | 8 (3) | 240 | 810 |
| **Total** | **180** | **25 (13)** | **750** | **3,510** |

- **Agent sessions** = 10 runs × 3 arms.
- **Check results** = checks × 30 agent sessions.
- **Judge calls** = judged checks × 30 agent sessions × 3 judges × 3 votes:
  1,170 each for `claude-opus-5-5`, `gpt-6-sol`, and `kimi-k3`.

That is **3,690 model sessions** in all: 180 agents writing code and 3,510
judge calls grading it.

## Cost

| Item | Cost |
|---|---:|
| No-plugin runs | $26.88 |
| This plugin's runs | $23.95 |
| Official plugin's runs | $31.88 |
| Re-judge with `gpt-6-sol` | $3.42 |
| Re-judge with `kimi-k3` | $6.14 |
| **Total** | **$92.27** |

The run costs include Opus judging during the run, $12.97 across all three
arms.

## Tokens

| Who | Sessions or calls | Cache writes | Cache reads | Uncached input | Output (thinking) |
|---|---:|---:|---:|---:|---:|
| Agent, no plugin | 60 | 1.97M | 21.07M | 1,206 | 562K (301K) |
| Agent, this plugin | 60 | 2.38M | 17.90M | 916 | 612K (382K) |
| Agent, official plugin | 60 | 2.46M | 25.00M | 1,244 | 668K (372K) |
| **Agent, all arms** | **180** | **6.80M** | **63.97M** | **3,366** | **1.84M (1.05M)** |
| Judge, `claude-opus-5-5` | 1,170 | — | — | not recorded | not recorded |
| Judge, `gpt-6-sol` | 1,170 | — | — | 1.53M | 35K |
| Judge, `kimi-k3` | 1,170 | — | — | 1.64M | 81K |

An agent session is many turns, and each turn rereads the conversation so far,
so almost all agent input comes from the cache. Agents with this plugin read
about 15% less than agents with no plugin, and about 28% less than agents with
the official one. The harness records the in-run judge's cost but not its
tokens. The counts are in each run's `usage.json` and `rejudge/`, and
`python3 evals/lib/usage.py --table evals/runs/<batch>-{none,this,official}`
prints them.

## How to read the numbers

- **Score.** The share of a case's checks a run passed, averaged over its 10
  runs. The ± is a 95% range from `compare.py`.
- **llm checks.** Each of three judges votes three times, and its own verdict is
  one vote on the panel. A check passes when two of the three judges pass it.
  The judges come from three providers, so no model family grades its own
  family alone. Opus votes during the run; `claude plugin eval` can call only
  Anthropic models, so `rejudge.py` adds the other two afterwards.
- **A check's lead.** With 10 runs, a small gap can be luck. A lead counts when a
  95% Newcombe interval on the two pass rates excludes zero. The cut-off is not
  a fixed gap: 10 against 6 counts, but 8 against 4 does not, because an arm
  that passes 8 of 10 could as easily have passed 6. `compare.py` marks each
  lead.
- **Only arms that ran together.** Arms from different launches of
  `EVAL_PLUGIN=all` do not compare.
  See [lessons.md](lessons.md).

## Every check

Passing runs out of 10, judged by the panel. The last two columns are this
plugin's count minus the other arm's.

- 🟢 **+8**: this plugin passed more often, by more than chance explains.
- +3: this plugin passed more often in these runs, but 10 runs cannot tell a
  gap this size from luck. `deterministic-backstop` against no plugin is one.
- −1: this plugin passed less often, by a margin just as small.
- 🔴 would mark this plugin falling behind by more than chance. No check does.

| Case | Check | No plugin | This plugin | Official | This plugin vs no plugin | This plugin vs official |
|---|---|---:|---:|---:|---:|---:|
| `command-gate` | `deterministic-backstop` | 7 | 10 | 2 | +3 | 🟢 **+8** |
|  | `max-not-average` | 10 | 10 | 10 | 0 | 0 |
|  | `no-noul-confidence` | 10 | 10 | 10 | 0 | 0 |
|  | `separate-flags` | 5 | 10 | 9 | 🟢 **+5** | +1 |
|  | `three-way-with-human-band` | 10 | 10 | 10 | 0 | 0 |
|  | `untrusted-reason-isolated` | 5 | 10 | 10 | 🟢 **+5** | 0 |
| `email-facts` | `counting-in-code` | 1 | 8 | 0 | 🟢 **+7** | 🟢 **+8** |
|  | `date-math-in-code` | 4 | 8 | 9 | +4 | −1 |
|  | `uses-date-objects` | 10 | 10 | 10 | 0 | 0 |
| `log-labeler` | `bounded-concurrency` | 7 | 10 | 6 | +3 | 🟢 **+4** |
|  | `no-hand-rolled-retry` | 9 | 10 | 10 | +1 | 0 |
|  | `one-client-reused` | 10 | 10 | 10 | 0 | 0 |
| `reply-grader` | `atomic-rubric` | 5 | 10 | 10 | 🟢 **+5** | 0 |
|  | `no-numeric-levels` | 10 | 10 | 10 | 0 | 0 |
|  | `refund-flag-high-means-bad` | 10 | 10 | 10 | 0 | 0 |
| `taxonomy-classify` | `keeps-more-than-one-path` | 1 | 10 | 7 | 🟢 **+9** | +3 |
|  | `no-choice-over-255` | 9 | 10 | 10 | +1 | 0 |
| `triage-ticket` | `choice-has-catch-all` | 3 | 10 | 6 | 🟢 **+7** | 🟢 **+4** |
|  | `no-hand-rolled-retry` | 7 | 10 | 10 | +3 | 0 |
|  | `points-at-state` | 0 | 10 | 1 | 🟢 **+10** | 🟢 **+9** |
|  | `probability-keys` | 8 | 10 | 4 | +2 | 🟢 **+6** |
|  | `records-model-version` | 0 | 10 | 0 | 🟢 **+10** | 🟢 **+10** |
|  | `routes-on-confidence` | 2 | 2 | 0 | 0 | +2 |
|  | `score-read-as-position` | 9 | 10 | 5 | +1 | 🟢 **+5** |
|  | `severity-premise` | 6 | 8 | 7 | +2 | +1 |

## What did not change

- **`routes-on-confidence`** passed 2 of 10 runs with this plugin, 2 with no
  plugin, and none with the official one. The check wants the code to branch on `confidence`, but the
  prompt never says what should happen to an uncertain ticket, so there is
  nowhere to send one. The skill's own advice agrees with the agents: when code
  only picks the best option, it needs no confidence threshold. The failing
  files return `confidence` to the caller and leave the decision there. The
  triage prompt now gives an uncertain ticket somewhere to go: "When the
  function is not sure enough of the department, the decision should send the
  ticket to a person instead." The next eval batch will show whether this
  check moves. Until then, `triage-ticket` scores from this batch do not
  compare with later ones.
- **`date-math-in-code`**, **`severity-premise`**, and `triage-ticket`'s
  **`no-hand-rolled-retry`** differ between arms by less than chance explains.
- **Nine checks passed almost every run in every arm.** They guard against
  mistakes this agent does not make on these tasks.

## One known wrong verdict

`no-hand-rolled-retry` failed no-plugin run 4 of `triage-ticket` on the words
"while triaging ticket" in an error message. The pattern now matches `while`
only at the start of a line. With the fixed pattern, that case's no-plugin score
is 0.45, not 0.44, and no mean moves. The tables show the eval batch as scored.

## Each judge

`gpt-6-sol` ran at effort medium and `kimi-k3` at effort high, with the prompt,
vote count, and vote rule the harness gives Opus. Each row scores the llm checks
with one judge alone.

| Judge | Agrees with Opus | No plugin | This plugin | Official |
|---|---:|---:|---:|---:|
| `claude-opus-5-5` (as run) | — | 0.66 ± 0.04 | 0.96 ± 0.02 | 0.77 ± 0.04 |
| `gpt-6-sol` | 381/390 | 0.65 ± 0.05 | 0.94 ± 0.03 | 0.75 ± 0.04 |
| `kimi-k3` | 382/390 | 0.66 ± 0.05 | 0.96 ± 0.02 | 0.77 ± 0.04 |
| **Majority of three** | — | **0.65 ± 0.05** | **0.96 ± 0.02** | **0.77 ± 0.04** |

The majority overturns 4 of Opus's 390 verdicts. Every arm's score, and both of
this plugin's leads, hold under each judge alone. Two checks split them:

- **`untrusted-reason-isolated`**: Kimi passed 9 of the 10 no-plugin runs that
  Opus and GPT-6 Sol passed 5 of. The majority gives 5.
- **`no-choice-over-255`**: GPT-6 Sol was stricter than Opus, with 5
  disagreements spread across all three arms.

Agreement shows the judges are consistent with each other, not that any of them
is right. Labeled pass and fail examples would measure that. The votes are in
each run's `rejudge/` directory, and `compare.py --as-run` prints the scores
with Opus alone.
