<p align="center">
  <img src="../assets/hero-en-x-aibro.png" alt="Building with TypeSafe Jev. Your coding agent treats Jev like one more chat model. This is the patch. Typed decisions. Calibrated confidence. 150+ community builds, clustered by shape. Two panels. On the left, labeled Structured Outputs, valid, not right: schema-valid JSON with next_step run_tests, pr_verdict meets spec, deletes_files false in red, and a confidence of 0.95, with the comments parses every time and confidence: sampled, not calibrated. On the right, labeled System One, 1 call, 100-200 ms: one Jev call returns three typed answers: a Choice (next_step: run tests, confidence 0.91), a Score (pr_vs_spec: 1.6 of 2), and a Noul (deletes_files: 0.97)." width="100%">
</p>

<p align="center">
  <strong>Building with TypeSafe Jev</strong><br>
  <em>Your coding agent treats Jev like one more chat model. This is the patch.</em><br>
  <em>Typed decisions. Calibrated confidence. 150+ community builds, clustered by shape.</em>
</p>

<p align="center">
  <a href="../../LICENSE"><img src="https://img.shields.io/github/license/aaddrick/building-with-typesafe-jev?style=flat" alt="License"></a>
  <a href="../workflows/checks.yml"><img src="https://img.shields.io/github/actions/workflow/status/aaddrick/building-with-typesafe-jev/checks.yml?label=checks&style=flat" alt="Checks"></a>
</p>

<p align="center">
  <a href="https://www.linkedin.com/in/aaddrick/">Connect on LinkedIn. The human in the loop is taking calls.</a>
</p>

<p align="center">
  <a href="../../README.md">English</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.ko.md">한국어</a> ·
  <a href="README.vi.md">Tiếng Việt</a> ·
  <a href="README.pt-BR.md">Português (BR)</a> ·
  <a href="README.it.md">Italiano</a> ·
  <strong>AI Bro</strong>
</p>

> [!NOTE]
> Full disclosure: this is an unofficial, community skill. TypeSafe AI did not build it, review it, or endorse it. Their first-party skill ships at [typesafe-ai/skills](https://github.com/typesafe-ai/skills). The honest comparison is in [How this differs from the official skill](#how-this-differs-from-the-official-skill).

We didn't build a Jev tutorial.

We built the grounding layer for every coding agent that treats Jev like one more chat model.

Typed primitives. Calibrated confidence. Progressive context loading. A prior-art knowledge base of 150+ community builds, clustered by implementation shape. Three agent harnesses on day one.

Prompt-and-parse had a good run. It's over.

## Install

<details>
<summary><strong>Claude Code</strong></summary>

Two commands. That's the whole onboarding.

```bash
claude plugin marketplace add aaddrick/building-with-typesafe-jev
```

```bash
claude plugin install building-with-typesafe-jev@building-with-typesafe-jev
```

No trigger phrase. No config. The skill loads itself into context the moment the task touches Jev code. Autonomous by default. Want the wheel back?

```
/building-with-typesafe-jev:building-with-typesafe-jev
```

The install may flag a plugin option as not set yet. Not a bug. That's live testing, off until you opt in. Safe by default. See [Set up an API key](#set-up-an-api-key-optional-strongly-recommended).

</details>

<details>
<summary><strong>Codex</strong></summary>

```bash
codex plugin marketplace add aaddrick/building-with-typesafe-jev
```

```bash
codex plugin add building-with-typesafe-jev@building-with-typesafe-jev
```

Start a new thread. Codex retrieves the skill when the task matches. Nobody has to ask. Manual invocation:

```
$building-with-typesafe-jev:building-with-typesafe-jev
```

</details>

<details>
<summary><strong>Antigravity CLI</strong></summary>

```bash
agy plugin install https://github.com/aaddrick/building-with-typesafe-jev
```

Confirm it's live:

```bash
agy plugin list
```

Spin up a new session. Antigravity CLI loads the skill the moment the task matches. Want to force it? Type:

```
/building-with-typesafe-jev:building-with-typesafe-jev
```

Migrating off Gemini CLI? If `agy plugin import gemini` carried this extension over, run the install command above anyway. It replaces the imported copy, whose settings command is dead weight in Antigravity CLI.

</details>

<details>
<summary><strong>Any other agent that reads SKILL.md</strong></summary>

Copy the `skills/building-with-typesafe-jev/` folder into your agent's skills folder. All of it. `SKILL.md` is a router, not a document: it links to the files beside it. Ship the router without the routes and you shipped a 404.

</details>

## Set up an API key (optional, strongly recommended)

Most agent tooling validates against its own imagination. Ground truth costs a fraction of a cent.

No key? The skill still ships. It picks the primitives, writes the questions and the code, and checks them against its API reference. Offline mode. Fully functional. Flying on instruments.

With a key, it validates against production: every design it proposes hits the real API before it hits your codebase. Wrong field names and questions Jev reads differently than you meant die in the probe, not in prod. The cheapest ground truth in the stack.

Live testing is opt-in. Off until you flip it. While it's off, the skill never even looks for a key. Zero discovery. Zero surprise. When it's on, it reads the key from exactly one place: the environment variable you name (`TYPESAFE_API_KEY` unless you pick another). It tells you before its first call and runs a capped probe: about 10 test calls per task. Three steps to production grounding: create a key, store it, turn on live testing.

<details>
<summary><strong>Create a key</strong> (four steps in the TypeSafe console)</summary>

**Step 1.** Sign in at [console.typesafe.ai](https://console.typesafe.ai/) and open **API Keys** in the sidebar.

<img src="../assets/api-key/step-1.png" alt="The TypeSafe console home page. An amber box and arrow point at API Keys in the left sidebar." width="100%">

**Step 2.** Click **Create key**, top right.

<img src="../assets/api-key/step-2.png" alt="The API keys page. Existing keys are blurred. An amber box and arrow point at the Create key button at the top right." width="100%">

**Step 3.** Name the key after where it will live: the machine, the agent. A key name is an observability primitive. Then click **Create key**.

<img src="../assets/api-key/step-3.png" alt="The Create API key dialog with the name my-coding-agent typed in. An amber box and arrow point at the name field and the Create key button." width="100%">

**Step 4.** Copy the key now. The console renders it once. One shot. No retries. Lose it and you rotate: create a new key, revoke the old one.

<img src="../assets/api-key/step-4.png" alt="The API key created dialog. The key value is masked. An amber box and arrow point at the Copy button." width="100%">

</details>

<details>
<summary><strong>Store the key</strong> (macOS, Linux, Windows)</summary>

One key. One file. One reader: you. The skill reads the key from an environment variable, never from a file. So the variable has to exist in the shells your agent spawns.

Here is the failure mode nobody documents. Agents spawn shells with no terminal attached. Headless. Non-interactive. Invisible to most setup guides. Every path below is context injection for those headless runtimes: the key exists where the agent actually runs. Pick your system.

<details>
<summary><strong>macOS</strong> (zsh, the default shell)</summary>

Write the key to a private file:

```bash
mkdir -p ~/.config/typesafe && umask 077 && printf 'export TYPESAFE_API_KEY=%s\n' 'YOUR_KEY' > ~/.config/typesafe/env
```

Load it from `~/.zshenv`. Every zsh reads that file, headless agent shells included. `~/.zshrc` runs for interactive shells only. Put the key there and your agent never sees it. Silent failure. The worst kind.

```bash
echo '[ -f ~/.config/typesafe/env ] && . ~/.config/typesafe/env' >> ~/.zshenv
```

New terminal. Verify. The command returns the key's length, never the key. Zero exfiltration surface:

```bash
echo ${#TYPESAFE_API_KEY}
```

</details>

<details>
<summary><strong>Linux with bash</strong> (Ubuntu, Debian, Mint, Fedora, Arch)</summary>

Write the key to a private file:

```bash
mkdir -p ~/.config/typesafe && umask 077 && printf 'export TYPESAFE_API_KEY=%s\n' 'YOUR_KEY' > ~/.config/typesafe/env
```

Load it from the **top** of `~/.bashrc`. Ubuntu, Debian, Mint, and Arch ship `~/.bashrc` with a guard that exits early when no terminal is attached. Everything below that guard is dead code to an agent. Line one runs on every distribution. Every one:

```bash
sed -i '1i [ -f ~/.config/typesafe/env ] \&\& . ~/.config/typesafe/env' ~/.bashrc
```

New terminal. Verify:

```bash
echo ${#TYPESAFE_API_KEY}
```

</details>

<details>
<summary><strong>Linux with zsh</strong></summary>

Follow the macOS steps. zsh reads `~/.zshenv` the same way on Linux. Same runtime, same fix.

</details>

<details>
<summary><strong>Linux with fish</strong></summary>

fish reads every file in `~/.config/fish/conf.d/`, terminal or not. No guard. No edge case. fish shipped the fix by default:

```fish
mkdir -p ~/.config/fish/conf.d; and echo 'set -gx TYPESAFE_API_KEY YOUR_KEY' > ~/.config/fish/conf.d/typesafe.fish; and chmod 600 ~/.config/fish/conf.d/typesafe.fish
```

```fish
string length -- $TYPESAFE_API_KEY
```

</details>

<details>
<summary><strong>Windows</strong> (PowerShell)</summary>

Store the key as a user environment variable. New terminals and apps inherit it. Terminals already open do not. Restart them. Stale context is still stale context:

```powershell
[Environment]::SetEnvironmentVariable('TYPESAFE_API_KEY', 'YOUR_KEY', 'User')
```

New terminal. Verify:

```powershell
$env:TYPESAFE_API_KEY.Length
```

**WSL:** Windows variables do not cross into WSL by default. Different runtime, different context. Inside WSL, follow the Linux with bash steps.

</details>

<details>
<summary><strong>Desktop apps and IDE extensions</strong></summary>

An app launched from the dock, the start menu, or a desktop launcher never reads your shell files. Different entry point. Different context window.

- **Windows:** the user environment variable above already covers these apps.
- **Linux (systemd):** add the line `TYPESAFE_API_KEY=YOUR_KEY` to `~/.config/environment.d/typesafe.conf`, then log out and back in.
- **macOS:** launch the app from a terminal, or set the variable in the app's own settings. macOS has no simple per-user file that desktop apps read. That one's on Cupertino.

</details>

</details>

<details>
<summary><strong>Turn on live testing</strong> (Claude Code, Codex, Antigravity CLI)</summary>

Every agent keeps two settings: live testing (`on` or `off`, default `off`) and the name of the variable that holds your key (default `TYPESAFE_API_KEY`). Set them once. They apply from the next session. The helper scripts need Python 3; the Codex one needs 3.11 or later. Legacy runtimes need not apply.

**Claude Code.** One command in your terminal:

```bash
claude plugin install building-with-typesafe-jev@building-with-typesafe-jev --config live_testing=on
```

Key living under a different name? Add `--config key_env_var=YOUR_VARIABLE`. Inside a session, `/plugin configure building-with-typesafe-jev@building-with-typesafe-jev` changes the same settings.

**Codex.** Codex has no plugin settings. So the skill keeps them in `~/.codex/config.toml`, which Codex passes to every shell the agent spawns. In a session, type:

```
$building-with-typesafe-jev:jev-settings live on
```

Codex asks you to approve the write. Human in the loop. Prefer the manual path? Add these lines to `~/.codex/config.toml`:

```toml
[shell_environment_policy.set]
JEV_LIVE_TESTING = "on"
JEV_KEY_ENV_VAR = "TYPESAFE_API_KEY"
```

One more gate: Codex wants you to trust the plugin's session-start hook, once. Every session, that hook tells the agent whether live testing is on and whether your key variable is set. The key itself? Never. Type `/hooks` in a session and trust it. An update that changes the hook means one more review. Skip it and nothing breaks: the hook just doesn't run, and the skill checks the settings on its own.

**Antigravity CLI.** No plugin settings. Zero config surface. The agent's shell inherits the environment of the terminal that launched `agy`, so the settings are just two environment variables, living right next to your key. Key in `~/.config/typesafe/env`? Run this, then open a new terminal and restart `agy`:

```bash
echo 'export JEV_LIVE_TESTING=on' >> ~/.config/typesafe/env
```

Key in a variable with another name? Add `export JEV_KEY_ENV_VAR=YOUR_VARIABLE` the same way. On fish or Windows, set `JEV_LIVE_TESTING` to `on` the way you stored the key.

**Verify.** Start a new session and run the settings command: `/building-with-typesafe-jev:jev-settings` in Claude Code, `$building-with-typesafe-jev:jev-settings` in Codex, or `/building-with-typesafe-jev:jev-settings` in Antigravity CLI. It shows both settings and whether the agent's shell can see the key. It prints the key's length, never the key. Observability without exfiltration.

**CI and containers.** The environment variables `JEV_LIVE_TESTING` and `JEV_KEY_ENV_VAR` override the saved settings in every agent. Infra-as-config, all the way down.

</details>

<details>
<summary><strong>If the agent cannot see the key</strong></summary>

The settings command says `key: not set in this shell` when the agent's shell has no such variable. Debug in this order:

- **You started the agent before you stored the key.** Agent shells inherit the environment of whatever launched them. Stale context. Quit the agent and start it from a new terminal.
- **You launched the agent from the dock, the start menu, or an IDE.** Those apps never read your shell files. See "Desktop apps and IDE extensions" above.
- **Codex filters the environment.** If `~/.codex/config.toml` sets `include_only` under `[shell_environment_policy]`, add your key variable, `JEV_LIVE_TESTING`, and `JEV_KEY_ENV_VAR` to it. If it sets `ignore_default_excludes = false`, Codex drops every variable with `KEY` in its name. Delete that line.
- **WSL.** Windows variables do not cross into WSL. Different runtime, different context. Store the key inside WSL with the Linux steps.

</details>

The skill never prints, logs, or hardcodes the key. It reads only the variable you name, and it hands the key to each test command without ever putting it on a command line. Transparency is not a setting. It's the default.

## What it does

Your LLM is not a decision engine. It's a text generator doing an impression of one.

You ask it to return JSON. It returns prose, then JSON, then an apology. So you write a parser. Then a retry loop. Then you switch on Structured Outputs: constrained decoding, schema-valid JSON on every call. Now it parses every time. It's still wrong some of the time, and nothing in the payload tells you how often.

A schema guarantees the shape, not the answer. The department field comes back "billing" either way: known or guessed, the JSON looks identical. Add a confidence field and the model writes a number, not a probability: sampled by the same decoder as the answer, calibrated against nothing. Congratulations: your routing logic branches on vibes, in valid JSON.

[Jev](https://docs.typesafe.ai/introduction) is a [System One](https://docs.typesafe.ai/concepts/system-one) model from TypeSafe AI. It does not write text. Its probabilities are optimized against outcomes, not sampled from a decoder, and most queries come back in 100 to 200 ms.

Input: some content, such as a support ticket, plus a set of questions. Output: one typed value and one calibrated probability per question. No prose to parse. No format to beg for. Three question types. That's the entire decision surface:

- **Choice** picks one option from a list you give. Example: an agent's next step, from search the docs, run the tests, or ask the user. Tool routing, no LLM in the loop.
- **Score** places the content on a scale that you describe step by step. Example: judge an agent's pull request on the scale ignores the spec → partly meets the spec → meets the spec. It lands at 1.6, most of the way to done. An eval judge with a real distribution behind it.
- **Noul** returns the probability that a yes/no statement is true. Example: "this shell command deletes files outside the project" comes back as 0.97. The approval gate trips before the command runs.

Jev launched on 2026-09-15. Reading the API reference is the easy part. Designing for a model that doesn't generate text is where coding agents fall over. We watched it happen: the agent finds one tutorial, hallucinates the rest of the API, and ports every prompt-and-parse habit into the one model built to end them.

This skill is the grounding layer: the API, the design rules, the known failure modes, and a map of what other people already built. The docs describe the model. This skill ships the design judgment.

## What changes

Same model. Same tasks. One variable. We ablated the skill. One coding agent, six Jev tasks, such as a support-ticket triage function and an approval gate for shell commands. The agent had the docs but no API key, so graders checked the code it wrote, not what that code did against Jev. Each task ran 10 times in each of three arms, all started together in one eval batch.

| | Control: no skill | Treatment: this skill | Official skill |
|---|---:|---:|---:|
| Average score | 0.65 | 0.96 | 0.77 |

A score is the share of checks a run passed. Each average is accurate to within 0.05, at 95% confidence. Error bars included, because we're not animals.

### Where this skill made the difference

These are the checks where the gap between treatment and control is too large to be chance, by a 95% test on the pass counts. Signal, not noise. Each number is how many of 10 runs passed.

| The agent's code... | Control: no skill | Treatment: this skill | Official skill |
|---|---:|---:|---:|
| counted in code, instead of asking Jev for a number | 1 | 8 | 0 |
| named a field of the input in its questions | 0 | 10 | 1 |
| pinned or logged the Jev model version | 0 | 10 | 0 |
| kept more than one path while walking 1,200 categories | 1 | 10 | 7 |
| gave the department list a catch-all option | 3 | 10 | 6 |
| asked the command gate more than one yes/no question | 5 | 10 | 9 |
| asked one question per rubric item and computed the grade in code | 5 | 10 | 10 |

A pattern match grades three of these checks. The other four go to three LLM judges from three providers, Claude Opus, GPT-6 Sol, and Kimi K3, and the majority decides. The agent is a Claude model, so a Claude judge never decides alone. Three judges. Majority rules.

### Against the official skill

Head to head, same test: this skill passed more often than the official skill on eight checks. Four are in the table: counting, field names, model version, and the catch-all. The other four:

- kept a plain-code rule that blocks a destructive command, or sends it to a person, whatever Jev says: 10 runs against 2
- read the severity probabilities by their integer keys: 10 against 4
- read `score` as a position from 0 to n-1: 10 against 5
- kept the log labeler to 8 or fewer requests at once: 10 against 6

### Where it made no difference

Full transparency: not every check moved.

- One check splits the judges, so it is not in the table. With Opus and GPT-6 Sol, this skill kept the agent's own reason from approving a command in 10 runs, against 5 with no skill. Kimi K3 passed 9 of those 10 no-skill runs. Different judge, different read.
- Routing on `confidence` passed 2 of 10 runs with this skill and 2 of 10 with no skill. Root cause: the task never said where an uncertain ticket should go, so most agents returned the confidence value and handed the call to the caller. The skill itself says that's fine when code only picks the best option. The task now names a fallback, and the next eval batch will test it.
- Every other check either passed in almost every run in all three arms, or differed by less than chance. Table stakes, or noise.

The [evals README](../../evals/README.md) has every check with its range, and how to run the suite.

## What is inside

Context is a budget. The lazy way to write a skill is one giant file: every endpoint, every edge case, every cookbook, loaded on every task. The agent pays for all of it in tokens and attention before it writes a line.

This one loads in layers. The agent pulls exactly the file the task needs, exactly when it needs it. Nothing more. Progressive disclosure: the only context strategy that scales.

| File | Payload | Retrieved when |
|---|---|---|
| `SKILL.md` | Which primitive to pick, 11 design rules, how to use probabilities and confidence, what to do when an answer is wrong, common mistakes | Every Jev task |
| `api-reference.md` | HTTP API, Python and JavaScript SDKs, limits, errors, environment variables | The agent writes the code |
| `patterns.md` | The 4 official patterns and techniques from 18 cookbooks, with their thresholds | The agent designs a workflow |
| `prior-art/INDEX.md` | A map from "what I want to build" to a shape, plus ideas that failed | Before the agent designs something new |
| `prior-art/*.md` | 11 shape files: a code sketch, field lessons, and linked projects | One or two per design |
| `scripts/jev_live.py` | Reads the live-testing settings, and runs a test command with the key | Right before a live test call |
| `../jev-settings/` | The settings command for Claude Code, Codex, and Antigravity CLI | When you run it |

## The prior-art library

Industry is the wrong embedding. Most catalogs sort projects by industry. Gaming. Robotics. Finance.

Wrong axis.

A game bot, a drone, and a trading bot are the same system: a control loop. Sort by implementation shape and three industries collapse into one cluster, with one code sketch and one set of field lessons. The 11 clusters:

- **Control loops**: games, drones, robots, markets.
- **Select from candidates**: browser and phone agents, tool calling without an LLM, extraction, routers.
- **Gates**: tool-call approval, "done" checks, CI, money, content.
- **Stream filters**: slop filters, moderation, email, logs, bulk labels.
- **Ranking and matching**: rerankers, entity matching, graph and taxonomy walks.
- **Judges and evals**: rubric judges, trace grading, code review as triage.
- **Incremental and real-time**: dubbing, voice, keystroke-driven interfaces.
- **Agent context and memory**: compaction, memory gates, memory expiry, effort control.
- **Pairing with an LLM**: planner and actor, verify-then-escalate, distillation.
- **Answers as data**: features for classical models, research instruments, benchmarks.
- **Embedding in infrastructure**: SQL functions, vector databases, CI hooks, Home Assistant.

And the part other catalogs leave out: the index ships the failures. Chess. Code review as the only reviewer. Perception. Calibration taken on trust.

Negative results are training signal. We keep them.

## How it was tested

We eval'd a README skill. Obviously.

Test-driven documentation. Red, green, refactor, applied to a folder of Markdown.

1. We ran a triage task with no skill and logged every guess and every mistake. That's the red.
2. We wrote the skill to kill exactly those mistakes. Nothing speculative.
3. A fresh agent ran the same task with the skill, then listed what was unclear. Six gaps. Six fixes.
4. We checked every API fact in the skill against the live API, with Python SDK 0.7.1 and model `jev-1.13.0`.
5. We ran three of the prior-art code sketches against the live API. One run surfaced that Jev reads hallucination checks literally. That lesson now ships in the skill.
6. A fresh agent tried three new designs with only the index. Right shape on all three. Two gaps flagged. Both closed.
7. We installed the plugin in Claude Code, Codex, and Antigravity CLI, and confirmed each one loads the skill. Green.
8. We ran six eval cases ten times each with this skill, with no skill, and with the official skill, each arm in its own isolated container. See [What changes](#what-changes) and the [evals README](../../evals/README.md).

## Keep it current

Every model has a knowledge cutoff. Including this one. Jev ships fast. This skill is a snapshot of [docs.typesafe.ai](https://docs.typesafe.ai/llms.txt) and of the community on 2026-09-25. That's its knowledge cutoff, and it knows it: the skill tells the agent the live docs win every conflict, and shows how to fetch them as Markdown.

Found a stale fact? Open an issue with a link to the source. That's the retraining loop.

## How this differs from the official skill

Respect to the first-party skill. The [official TypeSafe skill](https://github.com/typesafe-ai/skills) is lean: it points the agent at the live docs and retrieves at runtime. For current API details, it's the source of truth. Run it alongside this one.

Different architecture, different bet. This skill front-loads the context: the exact API shapes, the thresholds from the cookbooks, the failure modes from the community, the prior-art knowledge base. Zero network round trips at design time. The agent knows what the ecosystem already built before it writes line one.

The benchmark: on the six eval tasks, the official skill scored 0.77 ± 0.04, against 0.65 ± 0.05 with no skill and 0.96 ± 0.02 with this one. See the [evals README](../../evals/README.md).

## Credits

The API facts come from TypeSafe AI's public documentation and cookbooks. The prior art comes from the builders who shipped in public, from the Hacker News community, and from these indexes: [awesome-jev-typesafe](https://github.com/valentynkit/awesome-jev-typesafe), [JevDirectory](https://www.jevdirectory.org/resources), [awesome-jev-use-cases](https://github.com/walidboulanouar/awesome-jev-use-cases), and [awesome-typesafe-jev](https://github.com/AbdelStark/awesome-typesafe-jev). Every shape file links back to the original projects. Zero hallucinated citations.

TypeSafe, Jev, and System One are names of TypeSafe AI. This project uses them only to say what the skill is for.

## License

MIT. See [LICENSE](../../LICENSE). Fork it. Fine-tune it to your use case. Ship it.
