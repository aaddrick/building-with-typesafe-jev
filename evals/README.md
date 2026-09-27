# Evals

Does the skill change what a coding agent builds? Each of six cases is a task a
user might give an agent, such as "write a support-ticket triage function with
Jev." The same prompt runs in three arms: with this plugin, with no plugin, and
with TypeSafe's official plugin. Graders then check the code each agent wrote.
Checks that need judgment go to three LLM judges from three providers, and the
majority decides, so no model family grades its own family alone.

The agents get Jev's docs but no TypeSafe key, so they never call the API. The
checks read the code. They do not run it.

## Results

| | No plugin | This plugin | Official |
|---|---:|---:|---:|
| Mean score | 0.65 ± 0.05 | 0.96 ± 0.02 | 0.77 ± 0.04 |

A score is the share of checks a run passed. Each case ran 10 times per arm, all
three arms in one eval batch, with agent `claude-sonnet-5`. The judges are
`claude-opus-5-5`, `gpt-6-sol`, and `kimi-k3`. Each ± is a 95% range. This
plugin leads no plugin by +0.30 ± 0.05, and the official plugin by +0.19 ± 0.04.

| Case | No plugin | This plugin | Official |
|---|---:|---:|---:|
| `command-gate` | 0.78 ± 0.08 | 1.00 ± 0.00 | 0.85 ± 0.07 |
| `email-facts` | 0.50 ± 0.17 | 0.87 ± 0.17 | 0.63 ± 0.08 |
| `log-labeler` | 0.87 ± 0.12 | 1.00 ± 0.00 | 0.87 ± 0.12 |
| `reply-grader` | 0.83 ± 0.13 | 1.00 ± 0.00 | 1.00 ± 0.00 |
| `taxonomy-classify` | 0.50 ± 0.17 | 1.00 ± 0.00 | 0.85 ± 0.17 |
| `triage-ticket` | 0.44 ± 0.09 | 0.88 ± 0.00 | 0.41 ± 0.08 |

### Where the lead comes from

These are the checks where this plugin passed more runs than another arm, by
more than chance explains. Each number is passing runs out of 10.

| Check | No plugin | This plugin | Official | Ahead of |
|---|---:|---:|---:|---|
| `counting-in-code` | 1 | 8 | 0 | both |
| `points-at-state` | 0 | 10 | 1 | both |
| `records-model-version` | 0 | 10 | 0 | both |
| `choice-has-catch-all` | 3 | 10 | 6 | both |
| `keeps-more-than-one-path` | 1 | 10 | 7 | no plugin |
| `separate-flags` | 5 | 10 | 9 | no plugin |
| `atomic-rubric` | 5 | 10 | 10 | no plugin |
| `untrusted-reason-isolated` | 5 | 10 | 10 | no plugin, two judges to one |
| `deterministic-backstop` | 7 | 10 | 2 | official |
| `probability-keys` | 8 | 10 | 4 | official |
| `score-read-as-position` | 9 | 10 | 5 | official |
| `bounded-concurrency` | 7 | 10 | 6 | official |

[docs/cases.md](docs/cases.md) says what each check looks for.

### Read with care

- **The judges split on one lead.** Kimi K3 passed 9 of the 10 no-plugin runs
  of `untrusted-reason-isolated`. Opus and GPT-6 Sol passed 5, so the majority
  gives 5.
- **One check never moved.** `routes-on-confidence` passed 2 of 10 runs with
  this plugin, 2 with none, and 0 with the official one. The prompt never said
  where an uncertain ticket should go, so there was nothing to route. The prompt
  now names a fallback, and the next eval batch will test it. [docs/results.md](docs/results.md#what-did-not-change) has
  the details.
- **`log-labeler`'s lead over no plugin is marginal.** It clears its range by
  0.01.
- **The judges agree, but that does not make them right.** GPT-6 Sol and Kimi
  K3 each agree with Opus on about 98% of verdicts. Labeled examples would
  measure accuracy. There are none yet.

[docs/results.md](docs/results.md) has every check, each judge's scores, and the
method behind "more than chance."

## Run it

```bash
export CLAUDE_CODE_OAUTH_TOKEN=$(cat ~/.config/typesafe-eval-token)  # from `claude setup-token`
EVAL_PLUGIN=all evals/container/run.sh --runs 10 -j 4   # no plugin, this plugin, official: one container each
uv run --with openai python3 evals/lib/rejudge.py evals/runs/<batch>-{none,this,official}  # the other two judges
python3 evals/lib/compare.py <batch stamp>              # the tables above, judged by all three
```

This needs rootless podman, and keys for the other two judges on the host. A
full eval batch is 180 runs and costs about $95 with all three judges. Compare
arms only within one eval batch. [docs/harness.md](docs/harness.md#keep-an-eval-batch) has
the steps between the run and the re-judge.

## More

| File | What it covers |
|---|---|
| [LEDGER.md](LEDGER.md) | Every kept eval batch, with its commit, models, scores, and notes |
| [docs/results.md](docs/results.md) | The current baseline in full |
| [docs/harness.md](docs/harness.md) | How a run works: the container, the control, options, keeping an eval batch |
| [docs/cases.md](docs/cases.md) | The six cases and their 25 checks, and how to read a result |
| [docs/lessons.md](docs/lessons.md) | What broke while building the suite, and what each fix was |
