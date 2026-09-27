---
name: jev-settings
description: Use when the user asks to turn live TypeSafe Jev API testing on or off, to change which environment variable holds their TypeSafe API key, or to check those settings for the building-with-typesafe-jev skill.
disable-model-invocation: true
argument-hint: "[show | live on | live off | key-var NAME]"
---

# Jev settings

The `building-with-typesafe-jev` skill has two settings:

| Setting | Values | Default |
|---|---|---|
| Live testing | `on` or `off`. On lets the skill make about 10 real API calls per task, a fraction of a cent each. | `off` |
| Key variable | The **name** of the environment variable that holds the TypeSafe key. Never the key itself. | `TYPESAFE_API_KEY` |

Never ask for, print, or store the key's value. Only its variable name goes into a setting.

## 1. Show the current state

The status script belongs to the main skill. Use the first of these paths that your harness filled in:

- Claude Code: `${CLAUDE_PLUGIN_ROOT}/skills/building-with-typesafe-jev/scripts/jev_live.py`
- Codex and Antigravity CLI: `../building-with-typesafe-jev/scripts/jev_live.py`, relative to the folder that holds this SKILL.md

That path is `<status-script>` below. Your shell does not start in the skill folder, so write the full path. Copy the quoted arguments exactly as they appear, including any that still read `${...}`. Do not blank or remove them. Your harness fills in its own, and the script ignores the rest:

```bash
python3 <status-script> status --live '${user_config.live_testing}' --live '${JEV_LIVE_TESTING}' --key-var '${user_config.key_env_var}' --key-var '${JEV_KEY_ENV_VAR}'
```

On Windows, use `python` or `py -3` if `python3` is not found. Show the user the output.

## 2. Change a setting

With no arguments, ask the user two questions: turn live testing on or off, and which variable holds the key (offer `TYPESAFE_API_KEY`). Then save both. With arguments (`live on`, `live off`, `key-var NAME`), save only that one. A variable name must match `[A-Za-z_][A-Za-z0-9_]*`.

Save them the way your harness stores them. Every harness reads settings at session start, so tell the user the change applies to the next session.

**Claude Code** keeps them as plugin options. Run:

```bash
claude plugin install building-with-typesafe-jev@building-with-typesafe-jev --config live_testing=on --config key_env_var=TYPESAFE_API_KEY
```

Pass only the options being changed. If the command fails, tell the user to run `/plugin configure building-with-typesafe-jev@building-with-typesafe-jev` instead.

**Codex** keeps them in `~/.codex/config.toml` under `[shell_environment_policy.set]`. Run the script in this skill's folder (`<dir>`: the folder that holds this SKILL.md). Codex may ask to approve the write:

```bash
python3 <dir>/scripts/codex_settings.py set --live on --key-var TYPESAFE_API_KEY
```

It needs Python 3.11 or later. Pass only the options being changed. `python3 <dir>/scripts/codex_settings.py show` prints what is saved. If the script refuses to edit the file, show the user the lines it prints to paste in themselves.

**Antigravity CLI** has no plugin settings. Its shell inherits the environment of the terminal that started `agy`, so the settings are the environment variables below. Do not edit the user's shell files. Show the user the lines to add to their shell profile (`~/.bashrc`, `~/.zshrc`, or the file they keep their key in), then tell them to open a new terminal and restart `agy`:

```bash
export JEV_LIVE_TESTING=on
export JEV_KEY_ENV_VAR=TYPESAFE_API_KEY
```

Show only the lines for the options being changed. The key variable can be left out when it is `TYPESAFE_API_KEY`.

**Any harness:** the environment variables `JEV_LIVE_TESTING` and `JEV_KEY_ENV_VAR` override the saved settings. The status output says where each value came from. If a setting will not change, check whether one of these is set in the user's shell.

## 3. Check the key is visible

After turning live testing on, run step 1 again in the next session. `key: not set in this shell` means the agent's shell cannot see the variable. Point the user to the README section "If the agent cannot see the key".
