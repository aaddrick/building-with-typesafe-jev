# Eval harness

How a run works, and how to keep one. [cases.md](cases.md) covers the tasks and
checks. [lessons.md](lessons.md) covers what broke along the way.

## Layout

| Path | What it holds |
|---|---|
| `<case>/prompt.md` | The task. The agent sees only the body; the frontmatter sets run limits and tools. |
| `<case>/case.yaml` | Names the case, and its setup script if it has one. |
| `<case>/graders/*.md` | One check per file. |
| `taxonomy-classify/setup.sh` | Builds that case's fixture before the agent starts. |
| `container/` | The image, its entry script, and the launcher. |
| `run.sh` | Runs the suite on the host, without the container. |
| `lib/compare.py` | Scores an eval batch's arms with the three-judge panel, with a 95% range on every number. |
| `lib/keep_run.py` | Copies a finished run into `runs/`, with the file each agent wrote. |
| `lib/provenance.sh` | Records the commit a run used, and scrubs its traces. |
| `lib/rejudge.py` | Adds the two judges the harness cannot call, on the host only. |
| `lib/usage.py` | Copies each run's token counts out of its trace into `usage.json`. |
| `LEDGER.md` | One row per kept eval batch. |
| `runs/` | Kept runs: `aggregate-result.json`, `provenance.json`, `usage.json`, and `outputs/`. |
| `results/` | Raw output and traces. Git ignores it. |

## Run an eval batch

```bash
EVAL_PLUGIN=all evals/container/run.sh --runs 10 -j 4   # the three arms, one container each
python3 evals/lib/compare.py <batch stamp>              # the scores, with ranges
```

Each arm is one container running one harness process over one plugin:

| Arm | `EVAL_PLUGIN` | What the runs load |
|---|---|---|
| No plugin | `none` | The cases and nothing else: no skills, commands, hooks, or servers |
| This plugin | `this` | This repo's plugin, installed from GitHub at the commit checked out here |
| Official | `official` | `typesafe@typesafe-ai` at `EVAL_OFFICIAL_REF` |

`all` builds the image once and starts the three arms together, so they share a
time window and the same live docs. Their results directories share one batch
stamp. Arguments go to every arm, so `-j` is per arm: `-j 4` runs 12 at once.
Any arm can also run alone for a quick check.

**Cost.** A 10-run eval batch is 180 runs and cost $82.71 for the baseline, about
$0.46 a run. The agent is most of it; the in-run judge was $12.97 of the total.
Re-judging adds about $10. Each arm has its own ceiling, `EVAL_MAX_COST_USD`. `aggregate-result.json` gives
each run's `costUsd` and, within it, `judgeCostUsd`.

### Options

Arguments pass through to `claude plugin eval`, for example `--case
triage-ticket --runs 1`.

| Variable | Default | Effect |
|---|---|---|
| `EVAL_PLUGIN` | `this` | `this`, `official`, `none`, or `all` (all three in one eval batch) |
| `EVAL_OFFICIAL_REF` | `65a39f3…` | The `typesafe-ai/skills` commit an official run installs. Move it on purpose, and say so in the ledger. |
| `EVAL_MODEL` | `claude-sonnet-5` | The agent under test |
| `EVAL_JUDGE_MODEL` | `claude-opus-5-5` | The in-run judge, one of the three on the panel |
| `EVAL_MAX_COST_USD` | `60` | Cost ceiling per arm |
| `CLAUDE_CODE_OAUTH_TOKEN` | unset | Login for the container (below) |
| `EVAL_MIN_TOKEN_MINUTES` | `50` | Minimum life of the host's access token |

### Login

Set `CLAUDE_CODE_OAUTH_TOKEN` to a long-lived token from `claude setup-token`.
Otherwise `run.sh` passes the host's current OAuth access token, never the
refresh token, so the container cannot rotate your login. That token lasts
about an hour, so the script refuses to start with less than 50 minutes left.
Starting a new `claude` session does not refresh it early.

## Inside the container

The image is Fedora with Claude Code, Python, uv, bubblewrap, and socat, run in
rootless podman.

- **The repo is read-only.** Only `evals/results` is writable, and kept run
  directories land in `evals/results/tmp/` on the host.
- **No TypeSafe key.** Every arm works from the same docs, with no live calls.
- **Plugins come from GitHub at an exact commit.** The container clones over
  HTTPS, checks out the commit, and installs from that checkout's marketplace.
  `run.sh` refuses to test this plugin until its commit is pushed and nothing
  outside `evals/` differs from it, because the run tests GitHub's copy, not
  yours.
- **The cases stay out of the plugin.** The installed copy has no eval cases.
  The suite runs against a separate copy at `/tmp/plugin-under-test`, and the
  harness blocks reads of its `evals/` directory.

## How the control works

`claude plugin eval` starts every run as a fresh `claude -p` process with a
temporary home, working directory, and configuration. No arm sees your user
settings, `CLAUDE.md`, memory, other plugins, or installed skills, so the
control needs no instruction to avoid the skill. Every arm gets the same prompt
and the same tools.

Bash runs in Claude Code's bubblewrap sandbox. Writes stay in the run's home and
workspace, and the network reaches only the TypeSafe API, the TypeSafe docs, and
PyPI. WebSearch and WebFetch are open to every arm, so the control can find
tutorials the way a real agent would.

Every prompt ends with "Jev's docs are at https://docs.typesafe.ai." The
no-plugin arm stands for a developer who has the docs.

## Run on the host

```bash
evals/run.sh --runs 5 -j 8
```

This needs Claude Code 2.1.269 or later, and `bubblewrap` and `socat` for the
sandbox on Linux. It runs the plugin from the working tree. The host does not
wall off your home the way the container does, so use it to debug a case and
the container for scores you keep.

## Keep an eval batch

1. **Copy each arm into `runs/`.** Run
   `python3 evals/lib/keep_run.py evals/results/<dir> <id>` once per arm, with
   ids `<batch>-none`, `<batch>-this`, and `<batch>-official`. It copies
   the run's record and the file each agent wrote, as
   `outputs/<case>/with-<n>/<file>`, or a `MISSING` marker if there is none.
   Every arm runs with `--ablation none`, so the harness names every arm `with`;
   the directory says which arm it is.
2. **Re-judge it.** Run
   `uv run --with openai python3 evals/lib/rejudge.py evals/runs/<batch>-{none,this,official}`
   on the host. The score is the majority of three judges, and `compare.py`
   refuses to mix arms that were judged differently.
3. **Score it.** `python3 evals/lib/compare.py <batch>` prints the tables.
4. **Add a row to `LEDGER.md`** with the panel's scores, and notes on anything
   unusual.

Keep eval batches of 10 runs per arm. Use 5 for quick checks.

### What provenance records

Each run script writes `provenance.json` next to `aggregate-result.json`:

- the eval batch stamp, as `batch` (the 2026-09-26 baseline's record, written
  before the rename, calls it `session`)
- the commit the suite ran from, and any uncommitted file under `skills/`,
  `.claude-plugin/`, or `evals/` that shapes a run (docs, the ledger, and
  `runs/` do not count)
- the model each run's trace names, so the record shows what `EVAL_MODEL`
  resolved to
- the plugin commit each arm installed
- how many runs loaded each skill

It also writes `usage.json`: each run's token counts and cost, copied from the
end of its trace. The traces stay out of git, so this is the only kept record
of the agent's tokens.

### Why re-judging is a separate step

The agent under test is a Claude model, so a Claude judge alone could share its
blind spots. The panel adds `gpt-6-sol` and `kimi-k3`. `claude plugin eval` can
call only Anthropic models, so they judge afterwards, from the kept outputs,
with the harness's own prompt and vote rule. That needs no new agent runs.

`rejudge.py` runs on the host only. Keys come from `~/.config/eval-judges/env`,
never from the repo or a container. A full eval batch costs about $3.50 with
`gpt-6-sol` and $6.50 with `kimi-k3`. `rejudge.py --summary` prints each judge's
agreement with Opus.

### Traces

Traces in `evals/results/tmp/` hold whatever an agent read or printed. When a
run ends, the Claude login token and anything shaped like an Anthropic key are
replaced with `[REDACTED]`, and `provenance.json` records the count. The
harness seals each run's `home/` and `tmp/`. Those are never read or scrubbed,
so do not share them.
