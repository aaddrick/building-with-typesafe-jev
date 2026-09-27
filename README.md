<p align="center">
  <img src=".github/assets/hero.png" alt="Building with TypeSafe Jev: typed decisions with calibrated confidence, for your coding agent. Prior art from 150+ community projects, sorted by shape. Two panels. On the left, an LLM with Structured Outputs returns valid JSON: department billing, severity medium, refund false in red, and a confidence of 0.95 that is generated, not calibrated. On the right, one Jev call returns three typed answers: a Choice (department: billing, confidence 0.88), a Score (severity: 1.43 of 2), and a Noul (refund: 0.99)." width="100%">
</p>

<p align="center">
  <strong>Building with TypeSafe Jev</strong><br>
  <em>Typed decisions with calibrated confidence, for your coding agent.</em><br>
  <em>Prior art from 150+ community projects, sorted by shape.</em>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/aaddrick/building-with-typesafe-jev?style=flat" alt="License"></a>
  <a href=".github/workflows/checks.yml"><img src="https://img.shields.io/github/actions/workflow/status/aaddrick/building-with-typesafe-jev/checks.yml?label=checks&style=flat" alt="Checks"></a>
</p>

<p align="center">
  <a href="https://www.linkedin.com/in/aaddrick/">Connect on LinkedIn!</a>
</p>

<p align="center">
  <strong>English</strong> ·
  <a href=".github/readme/README.zh-CN.md">简体中文</a> ·
  <a href=".github/readme/README.ja.md">日本語</a> ·
  <a href=".github/readme/README.ko.md">한국어</a> ·
  <a href=".github/readme/README.vi.md">Tiếng Việt</a> ·
  <a href=".github/readme/README.pt-BR.md">Português (BR)</a> ·
  <a href=".github/readme/README.it.md">Italiano</a> ·
  <a href=".github/readme/README.en-x-aibro.md">AI Bro</a>
</p>

> [!NOTE]
> This is an unofficial, community skill. It is not made, reviewed, or endorsed by TypeSafe AI. TypeSafe publishes its own skill at [typesafe-ai/skills](https://github.com/typesafe-ai/skills). See [How this differs from the official skill](#how-this-differs-from-the-official-skill).

Coding agents treat Jev like one more chat model. This skill teaches them to design for it: typed questions, calibrated confidence, and a library of 150+ community projects sorted by how they work. It installs in Claude Code, Codex, and Antigravity CLI.

## Install

<details>
<summary><strong>Claude Code</strong></summary>

Run these two commands in your terminal:

```bash
claude plugin marketplace add aaddrick/building-with-typesafe-jev
```

```bash
claude plugin install building-with-typesafe-jev@building-with-typesafe-jev
```

The skill loads on its own when you work on Jev code. To load it by hand, type:

```
/building-with-typesafe-jev:building-with-typesafe-jev
```

The install may say that a plugin option is not set yet. That is live testing, which stays off until you turn it on. See [Set up an API key](#set-up-an-api-key-optional-recommended).

</details>

<details>
<summary><strong>Codex</strong></summary>

```bash
codex plugin marketplace add aaddrick/building-with-typesafe-jev
```

```bash
codex plugin add building-with-typesafe-jev@building-with-typesafe-jev
```

Start a new thread. Codex loads the skill when the task matches. To load it by hand, type:

```
$building-with-typesafe-jev:building-with-typesafe-jev
```

</details>

<details>
<summary><strong>Antigravity CLI</strong></summary>

```bash
agy plugin install https://github.com/aaddrick/building-with-typesafe-jev
```

Check that it installed:

```bash
agy plugin list
```

Start a new session. Antigravity CLI loads the skill when the task matches. To load it by hand, type:

```
/building-with-typesafe-jev:building-with-typesafe-jev
```

Coming from Gemini CLI? If `agy plugin import gemini` brought this extension over, run the install command above anyway. It replaces the imported copy, whose settings command does not work in Antigravity CLI.

</details>

<details>
<summary><strong>Any other agent that reads SKILL.md</strong></summary>

Copy the `skills/building-with-typesafe-jev/` folder into your agent's skills folder. Keep the whole folder. `SKILL.md` links to the files beside it.

</details>

## Set up an API key (optional, recommended)

The skill works without a key. It still picks the primitives, writes the questions and the code, and checks them against its API reference. With a key, it also tests each design with real API calls before the code reaches your project. That catches wrong field names and questions Jev reads differently than you meant. Each call costs a fraction of a cent, so we strongly suggest a key.

Live testing is off until you turn it on. While it is off, the skill never looks for a key. When it is on, it reads the key only from the environment variable you name (`TYPESAFE_API_KEY` unless you pick another), tells you before its first call, and keeps to about 10 test calls per task. Three steps: create a key, store it, and turn on live testing.

<details>
<summary><strong>Create a key</strong> (four steps in the TypeSafe console)</summary>

**Step 1.** Sign in at [console.typesafe.ai](https://console.typesafe.ai/) and open **API Keys** in the sidebar.

<img src=".github/assets/api-key/step-1.png" alt="The TypeSafe console home page. An amber box and arrow point at API Keys in the left sidebar." width="100%">

**Step 2.** Click **Create key** at the top right.

<img src=".github/assets/api-key/step-2.png" alt="The API keys page. Existing keys are blurred. An amber box and arrow point at the Create key button at the top right." width="100%">

**Step 3.** Name the key after where it will live, such as the machine or the agent. Then click **Create key**.

<img src=".github/assets/api-key/step-3.png" alt="The Create API key dialog with the name my-coding-agent typed in. An amber box and arrow point at the name field and the Create key button." width="100%">

**Step 4.** Copy the key now. The console shows it once. If you lose it, create a new one and revoke the old one.

<img src=".github/assets/api-key/step-4.png" alt="The API key created dialog. The key value is masked. An amber box and arrow point at the Copy button." width="100%">

</details>

<details>
<summary><strong>Store the key</strong> (macOS, Linux, Windows)</summary>

Keep the key in its own file, readable only by you. The skill reads the key from an environment variable, never from a file, so the variable must be set in the shells your agent starts. Agents often start shells without a terminal, so each section puts the key where those shells can see it. Pick your system.

<details>
<summary><strong>macOS</strong> (zsh, the default shell)</summary>

Save the key to a private file:

```bash
mkdir -p ~/.config/typesafe && umask 077 && printf 'export TYPESAFE_API_KEY=%s\n' 'YOUR_KEY' > ~/.config/typesafe/env
```

Load it from `~/.zshenv`. Every zsh reads that file, including shells that agents start without a terminal. `~/.zshrc` is read only by interactive shells.

```bash
echo '[ -f ~/.config/typesafe/env ] && . ~/.config/typesafe/env' >> ~/.zshenv
```

Open a new terminal and check it. The command prints the length of the key, not the key:

```bash
echo ${#TYPESAFE_API_KEY}
```

</details>

<details>
<summary><strong>Linux with bash</strong> (Ubuntu, Debian, Mint, Fedora, Arch)</summary>

Save the key to a private file:

```bash
mkdir -p ~/.config/typesafe && umask 077 && printf 'export TYPESAFE_API_KEY=%s\n' 'YOUR_KEY' > ~/.config/typesafe/env
```

Load it from the **top** of `~/.bashrc`. Ubuntu, Debian, Mint, and Arch start `~/.bashrc` with a line that stops early when no terminal is attached. A line below that guard never runs for agent shells. The top of the file is safe on every distribution:

```bash
sed -i '1i [ -f ~/.config/typesafe/env ] \&\& . ~/.config/typesafe/env' ~/.bashrc
```

Open a new terminal and check it:

```bash
echo ${#TYPESAFE_API_KEY}
```

</details>

<details>
<summary><strong>Linux with zsh</strong></summary>

Follow the macOS steps. zsh reads `~/.zshenv` the same way on Linux.

</details>

<details>
<summary><strong>Linux with fish</strong></summary>

fish reads every file in `~/.config/fish/conf.d/`, with or without a terminal:

```fish
mkdir -p ~/.config/fish/conf.d; and echo 'set -gx TYPESAFE_API_KEY YOUR_KEY' > ~/.config/fish/conf.d/typesafe.fish; and chmod 600 ~/.config/fish/conf.d/typesafe.fish
```

```fish
string length -- $TYPESAFE_API_KEY
```

</details>

<details>
<summary><strong>Windows</strong> (PowerShell)</summary>

Store the key as a user environment variable. New terminals and apps see it. Terminals that are already open do not:

```powershell
[Environment]::SetEnvironmentVariable('TYPESAFE_API_KEY', 'YOUR_KEY', 'User')
```

Open a new terminal and check it:

```powershell
$env:TYPESAFE_API_KEY.Length
```

**WSL:** Windows variables do not reach WSL by default. Inside WSL, follow the Linux with bash steps.

</details>

<details>
<summary><strong>Desktop apps and IDE extensions</strong></summary>

An app you start from the dock, the start menu, or a desktop launcher does not read your shell files.

- **Windows:** the user environment variable above already covers these apps.
- **Linux (systemd):** add the line `TYPESAFE_API_KEY=YOUR_KEY` to `~/.config/environment.d/typesafe.conf`, then log out and back in.
- **macOS:** start the app from a terminal, or set the variable in the app's own settings. macOS has no simple per-user file that desktop apps read.

</details>

</details>

<details>
<summary><strong>Turn on live testing</strong> (Claude Code, Codex, Antigravity CLI)</summary>

Each agent keeps two settings: live testing (`on` or `off`, default `off`) and the name of the variable that holds your key (default `TYPESAFE_API_KEY`). Set them once. They apply from the next session. The helper scripts need Python 3; the Codex one needs 3.11 or later.

**Claude Code.** Run this in your terminal:

```bash
claude plugin install building-with-typesafe-jev@building-with-typesafe-jev --config live_testing=on
```

If your key is in a variable with another name, add `--config key_env_var=YOUR_VARIABLE`. In a session, `/plugin configure building-with-typesafe-jev@building-with-typesafe-jev` changes the same settings.

**Codex.** Codex has no plugin settings, so the skill keeps them in `~/.codex/config.toml`, which Codex passes to every shell the agent starts. In a session, type:

```
$building-with-typesafe-jev:jev-settings live on
```

Codex asks to approve the write. To make the change by hand, add these lines to `~/.codex/config.toml`:

```toml
[shell_environment_policy.set]
JEV_LIVE_TESTING = "on"
JEV_KEY_ENV_VAR = "TYPESAFE_API_KEY"
```

Codex also asks you to trust the plugin's session-start hook once. At the start of each session, the hook tells the agent whether live testing is on and whether your key variable is set, never the key itself. In a session, type `/hooks` and trust it. Codex asks again when an update changes the hook. Until you trust it, the hook does not run, and the skill still checks the settings itself.

**Antigravity CLI.** Antigravity CLI has no plugin settings, but the agent's shell inherits the environment of the terminal that started `agy`. So the settings are two environment variables, set where you stored the key. With the key in `~/.config/typesafe/env`, run this, then open a new terminal and restart `agy`:

```bash
echo 'export JEV_LIVE_TESTING=on' >> ~/.config/typesafe/env
```

If your key is in a variable with another name, add `export JEV_KEY_ENV_VAR=YOUR_VARIABLE` the same way. On fish or Windows, set `JEV_LIVE_TESTING` to `on` the way you stored the key.

**Check it.** Start a new session and run the settings command: `/building-with-typesafe-jev:jev-settings` in Claude Code, `$building-with-typesafe-jev:jev-settings` in Codex, or `/building-with-typesafe-jev:jev-settings` in Antigravity CLI. It shows both settings and whether the agent's shell can see the key. It prints the key's length, never the key.

**CI and containers.** The environment variables `JEV_LIVE_TESTING` and `JEV_KEY_ENV_VAR` override the saved settings in every agent.

</details>

<details>
<summary><strong>If the agent cannot see the key</strong></summary>

The settings command says `key: not set in this shell` when the agent's shell has no such variable. Check these in order:

- **You started the agent before you stored the key.** Agent shells copy the environment of the program that started them. Quit the agent and start it from a new terminal.
- **You started the agent from the dock, the start menu, or an IDE.** Those apps do not read your shell files. See "Desktop apps and IDE extensions" above.
- **Codex filters the environment.** If `~/.codex/config.toml` sets `include_only` under `[shell_environment_policy]`, add your key variable, `JEV_LIVE_TESTING`, and `JEV_KEY_ENV_VAR` to it. If it sets `ignore_default_excludes = false`, Codex drops every variable with `KEY` in its name. Remove that line.
- **WSL.** Windows variables do not reach WSL. Store the key inside WSL with the Linux steps.

</details>

The skill never prints, logs, or hardcodes the key. It reads only the variable you name, and it hands the key to each test command without putting the key on a command line.

## What it does

An LLM can return JSON, and with Structured Outputs the JSON parses every time. It can still be wrong, and nothing in the output tells you how often. A schema fixes the shape of the answer, not the answer. The department field says "billing" whether the model knew or guessed. If you add a confidence field, the model writes that number the same way it writes the answer. The number is not calibrated against anything.

[Jev](https://docs.typesafe.ai/introduction) is a [System One](https://docs.typesafe.ai/concepts/system-one) model from TypeSafe AI. It does not write text. Its probabilities are optimized against outcomes, not sampled from a decoder, and most queries return in 100 to 200 ms. You send it some content, such as a support ticket, and a set of questions. It answers each question with a typed value and a calibrated probability. There is no text to parse. A question comes in one of three types:

- **Choice** picks one option from a list you give. Example: an agent's next step, from search the docs, run the tests, or ask the user. That is tool routing with no LLM in the loop.
- **Score** places the content on a scale that you describe step by step. Example: grade an agent's pull request on the scale ignores the spec → partly meets the spec → meets the spec. It lands at 1.6, most of the way to meeting the spec.
- **Noul** gives the probability that a yes/no statement is true. Example: "this shell command deletes files outside the project" comes back as 0.97, and an approval gate stops the command before it runs.

Reading the API reference is the easy part. The hard part is designing for a model that does not write text. An agent without this skill finds one tutorial, guesses the rest of the API, and brings prompt-and-parse habits to a model built to replace them. This skill gives the agent the API, the design rules, the known failure modes, and a map of what other people already built. The docs describe the model. The skill shows how to design for it.

## What changes

We gave a coding agent six Jev tasks, such as a support-ticket triage function and an approval gate for shell commands. The agent had the docs but no API key, so graders checked the code it wrote, not what that code did against Jev. Each task ran 10 times in each of three setups, all started together in one eval batch.

| | No skill | This skill | Official skill |
|---|---:|---:|---:|
| Average score | 0.65 | 0.96 | 0.77 |

A score is the share of checks a run passed. Each average is accurate to within 0.05, at 95% confidence.

### Where this skill made the difference

These are the checks where the gap between this skill and no skill is too large to be chance, by a 95% test on the pass counts. Each number is how many of 10 runs passed.

| The agent's code... | No skill | This skill | Official skill |
|---|---:|---:|---:|
| counted in code, instead of asking Jev for a number | 1 | 8 | 0 |
| named a field of the input in its questions | 0 | 10 | 1 |
| pinned or logged the Jev model version | 0 | 10 | 0 |
| kept more than one path while walking 1,200 categories | 1 | 10 | 7 |
| gave the department list a catch-all option | 3 | 10 | 6 |
| asked the command gate more than one yes/no question | 5 | 10 | 9 |
| asked one question per rubric item and computed the grade in code | 5 | 10 | 10 |

A pattern match grades three of these checks. The other four go to three LLM judges from three providers, Claude Opus, GPT-6 Sol, and Kimi K3, and the majority decides. The agent is a Claude model, so a Claude judge never decides alone.

### Against the official skill

By the same test, this skill passed more often than the official skill on eight checks. Four are in the table: counting, field names, model version, and the catch-all. The other four:

- kept a plain-code rule that blocks a destructive command, or sends it to a person, whatever Jev says: 10 runs against 2
- read the severity probabilities by their integer keys: 10 against 4
- read `score` as a position from 0 to n-1: 10 against 5
- kept the log labeler to 8 or fewer requests at once: 10 against 6

### Where it made no difference

- One check splits the judges, so it is not in the table. With Opus and GPT-6 Sol, this skill kept the agent's own reason from approving a command in 10 runs, against 5 with no skill. Kimi K3 passed 9 of those 10 no-skill runs.
- Routing on `confidence` passed 2 of 10 runs with this skill and 2 of 10 with no skill. The task never said where an uncertain ticket should go, so most agents returned the confidence value and left the decision to the caller. The skill itself says that is fine when code only picks the best option. The task now names a fallback, and the next eval batch will test it.
- Every other check either passed in almost every run in all three setups, or differed by less than chance.

The [evals README](evals/README.md) has every check with its range, and how to run the suite.

## What is inside

The skill loads in layers, so the agent reads only what the task needs. One big file would cost the agent tokens and attention on every task, before it writes a line of code.

| File | What it holds | When the agent reads it |
|---|---|---|
| `SKILL.md` | Which primitive to pick, 11 design rules, how to use probabilities and confidence, what to do when an answer is wrong, common mistakes | Every Jev task |
| `api-reference.md` | HTTP API, Python and JavaScript SDKs, limits, errors, environment variables | When it writes the code |
| `patterns.md` | The 4 official patterns and techniques from 18 cookbooks, with their thresholds | When it designs a workflow |
| `prior-art/INDEX.md` | A map from "what I want to build" to a shape, plus ideas that failed | Before it designs something new |
| `prior-art/*.md` | 11 shape files: a code sketch, field lessons, and linked projects | One or two per design |
| `scripts/jev_live.py` | Reads the live-testing settings, and runs a test command with the key | Before a live test call |
| `../jev-settings/` | The settings command for Claude Code, Codex, and Antigravity CLI | When you run it |

## The prior-art library

Most catalogs sort projects by industry. This library sorts them by implementation shape. A game bot, a drone, and a trading bot share one shape: a control loop. Sorted that way, the three share one code sketch and one set of field lessons. The 11 shapes:

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

The index also lists the ideas that failed in the field: chess, code review as the only reviewer, perception, and calibration taken on trust. A failed attempt saves the next builder from repeating it.

## How it was tested

We tested the skill the way you test code: watch it fail first, then fix it.

1. We ran a triage task with no skill and wrote down every guess and every mistake.
2. We wrote the skill to fix those mistakes.
3. A fresh agent ran the same task with the skill, then listed what was unclear. We fixed six gaps.
4. We checked the API facts in the skill against the live API, with Python SDK 0.7.1 and model `jev-1.13.0`.
5. We ran three of the prior-art code sketches against the live API. One run showed that Jev reads hallucination checks literally, and that lesson is now in the skill.
6. A fresh agent tried three new designs with only the index. It found the right shape for each and reported two gaps. We fixed both.
7. We installed the plugin in Claude Code, Codex, and Antigravity CLI, and checked that each one loads the skill.
8. We ran six eval cases ten times each with this skill, with no skill, and with the official skill, each arm in its own isolated container. See [What changes](#what-changes) and the [evals README](evals/README.md).

## Keep it current

Jev changes fast. The skill is a snapshot of [docs.typesafe.ai](https://docs.typesafe.ai/llms.txt) and of the community on 2026-09-25. It tells the agent that the live docs win on any conflict, and it shows how to fetch them as Markdown. When a fact in the skill is wrong, please open an issue with a link to the source.

## How this differs from the official skill

The [official TypeSafe skill](https://github.com/typesafe-ai/skills) is short and points the agent at the live docs. It is the right source for current API details. Install it too if you want.

This skill holds more inside the skill itself: the exact API shapes, the thresholds from the cookbooks, the failure modes from the community, and the prior-art library. An agent can design without a network round trip, and it can find what others built before it starts.

On the six eval tasks, the official skill scored 0.77 ± 0.04, against 0.65 ± 0.05 with no skill and 0.96 ± 0.02 with this one. See the [evals README](evals/README.md).

## Credits

The facts about the API come from TypeSafe AI's public documentation and cookbooks. The prior art comes from the builders who published their projects, from the Hacker News community, and from these indexes: [awesome-jev-typesafe](https://github.com/valentynkit/awesome-jev-typesafe), [JevDirectory](https://www.jevdirectory.org/resources), [awesome-jev-use-cases](https://github.com/walidboulanouar/awesome-jev-use-cases), and [awesome-typesafe-jev](https://github.com/AbdelStark/awesome-typesafe-jev). Each shape file links to the original projects.

TypeSafe, Jev, and System One are names of TypeSafe AI. This project uses them only to say what the skill is for.

## License

MIT. See [LICENSE](./LICENSE).
