# Lessons learned

Each of these cost at least one run while the suite was being built, and each
is fixed. They are written down so the next person can make new, more
interesting mistakes.

## Environment

- **No `/proc` in the sandbox.** Rootless podman blocks bubblewrap's `/proc`
  mount, and every Bash call fails with `Can't mount proc on /proc`. The
  container passes `--security-opt unmask=/proc/*`.
- **Variables do not reach the sandbox.** Runs inherit only an allowlist, plus
  `EVAL_*`, and Bash inside the sandbox does not see `EVAL_*` either. Pass what a
  run needs in a file the setup script writes.
- **The harness owns the run's settings file.** A setup script cannot add to it
  (the harness refuses to start when the file exists), and the run ignores
  `.claude/settings.json` in the workspace. Managed settings are the one way to
  add a hook to every arm.
- **The harness calls only Anthropic models.** A judge from another provider
  cannot run inside `claude plugin eval`, so the other two judges run
  afterwards from the kept outputs. That is why `keep_run.py` copies the file
  each agent wrote.
- **The trace format changes under you.** A `permission_denied` event carries its
  `message` as a string, not an object, and the provenance step crashed on it
  after scoring. The parser now skips anything that is not an object.

## Keeping the control blind

- **The sandbox's deny list is visible to every arm.** When the plugin under test
  sat in the plugin cache, the deny list named its path, and control agents read
  the name and went looking. Reads were blocked, but runs wasted turns. The
  neutral path `/tmp/plugin-under-test` fixes it.
- **A prompt that does not name the docs measures something else.** Without the
  docs URL, most no-plugin runs wrote no file. Some asked for docs without
  searching, and one found the SDK repo under several GitHub accounts and
  stopped over a supply-chain worry. The score measured whether the agent had
  heard of Jev, not the code it wrote. Every prompt now names the docs.

## Graders

- **A grader can be stricter than the skill.** A model-version check once
  required `jev-x.y.z`, but the skill pins only when thresholds were tuned
  against a version, and otherwise logs `response.model`. `points-at-state` once
  required a dotted path, so a plain field name did not count. Now
  `records-model-version` accepts either, and `points-at-state` is an llm check,
  because a regex cannot tell a question's text from a docstring.
- **A pattern can match words in a string.** `no-hand-rolled-retry` once matched
  `while` anywhere on a line, including the error message "rate limit exceeded
  while triaging ticket". It now matches `while` only at the start of a line.
- **A check every arm passes only lifts every score.** Checks that the agent
  wrote its file passed in every run once prompts named the docs, and were cut.
  `probability-keys` and `no-hand-rolled-retry` passed every run until the
  triage prompt gave the agent a reason to read probabilities and handle rate
  limits.

## Skill text

- **`$0` in `SKILL.md` is a placeholder.** Claude Code substitutes argument
  placeholders in skill text, so a price like `$0.001` arrived as
  `Writing.001`. Only `SKILL.md` is affected; files it links to are read as-is.
  Write prices there without a `$` before a digit.

## Comparing

- **Eval batches drift.** The unchanged no-plugin arm of `command-gate` scored
  0.88 in one eval batch and 0.93 in the next. Compare arms only within one
  eval batch. That is why `EVAL_PLUGIN=all` starts the three together.
