# Cases and checks

Each case is a task a user might give a coding agent, built on a shape from
`skills/building-with-typesafe-jev/prior-art/`. Each one sets a trap that the
skill warns about, and each check looks for one trap.

## The checks

| Case | Shape | Check | Passes when | Type |
|---|---|---|---|---|
| `triage-ticket` | README table | `score-read-as-position` | Uses `score` as a 0 to n-1 position | llm |
| | | `probability-keys` | Never reads probabilities by string key | regex |
| | | `routes-on-confidence` | Branches on `confidence` | regex |
| | | `severity-premise` | The severity question states its premise | llm |
| | | `choice-has-catch-all` | The department Choice has a catch-all option | regex |
| | | `points-at-state` | The state is a named object, and a question names one of its fields | llm |
| | | `no-hand-rolled-retry` | No retry loop around the SDK | regex |
| | | `records-model-version` | Pins `jev-x.y.z` or reads `response.model` | regex |
| `command-gate` | Gates | `separate-flags` | Asks at least two Noul questions | regex |
| | | `no-noul-confidence` | Does not read `.confidence` from a Noul | regex |
| | | `max-not-average` | Does not average flags | regex |
| | | `untrusted-reason-isolated` | The agent's reason has its own field and cannot approve alone | llm |
| | | `deterministic-backstop` | A code rule can block a destructive command, or send it to a person, whatever Jev says | llm |
| | | `three-way-with-human-band` | Approve, block, or ask, with a middle band for the human | llm |
| `email-facts` | Rule 10 | `counting-in-code` | No question asks Jev to count | llm |
| | | `date-math-in-code` | No question asks Jev to compare dates | llm |
| | | `uses-date-objects` | Compares dates in Python | regex |
| `taxonomy-classify` | Ranking: walk | `no-choice-over-255` | No Choice over more than 255 options | llm |
| | | `keeps-more-than-one-path` | Beam search or a fallback, not greedy only | llm |
| `log-labeler` | Stream filters | `bounded-concurrency` | No more than 8 requests at once | regex |
| | | `no-hand-rolled-retry` | No retry loop around the SDK | regex |
| | | `one-client-reused` | One client for all lines | llm |
| `reply-grader` | Judges | `atomic-rubric` | One question per criterion, with the grade computed in code | llm |
| | | `no-numeric-levels` | Score levels are situations, not numbers | regex |
| | | `refund-flag-high-means-bad` | The refund Noul reads yes = bad | llm |

Whether a skill loaded is not a check. `provenance.json` counts the runs that
loaded each skill.

`taxonomy-classify`'s `setup.sh` builds its `taxonomy.json` (12 × 10 × 10 =
1,200 leaves), so both run scripts pass `--scaffold`.

## How checks are graded

- **Regex checks** read the agent's file the same way every time. Every pattern
  has match and no-match strings in `tests/test_eval_graders.py`. Add a string
  there whenever you change a pattern.
- **llm checks** cover rules a regex cannot judge, such as whether a question's
  text names a field. Three judges from three providers each vote three times,
  and a check passes when two of the three judges pass it. Opus votes during the
  run and the other two afterwards; [harness.md](harness.md#why-re-judging-is-a-separate-step)
  says why. A missing file fails.

## Writing a check

- **Make the trap reachable.** A check for a bad pattern passes when the code
  never does the thing at all. The triage prompt asks how likely the most severe
  level is, which means reading the severity Score's `probabilities`, and says
  the function must cope with rate limits, which invites a retry loop. It also
  says uncertain tickets go to a person, so there is a reason to branch on
  `confidence`.
- **Check the behavior, not a spelling.** `no-hand-rolled-retry` looks for a
  loop or a sleep, not for catching the rate-limit error, which code may do to
  surface it.
- **A check every arm passes tells you nothing.** Cut it, or change the prompt
  so the trap is live.

## Reading a result

- Compare arms only within one eval batch, and read every number with its range.
- A difference inside the range is noise. So is a single llm-graded flip
  between arms, until repeat runs agree.
- When every arm fails a check, or a regex fails a file, read the file before
  trusting the grader.
- Some runs stop without writing a file. Read the report for those before
  taking a low score as bad code.
- Publish every number with its model, judge, run count, and Claude Code
  version. `aggregate-result.json` carries all four.
