#!/usr/bin/env python3
"""Live-testing helper for the building-with-typesafe-jev skill. Standard library only.

  status  Resolve the live-testing settings and say whether the key variable is set.
          Prints the key's length, never its value.
  exec    Run one command with TYPESAFE_API_KEY taken from the configured variable.
          Only that command and its children see the copy. The value never appears
          on a command line, in the transcript, or in shell history.
  hook    SessionStart hook for Claude Code and Codex. Prints the two settings and
          whether the key variable is set, for the agent's context. Never fails.

Settings, highest priority first:
  1. The environment: JEV_LIVE_TESTING and JEV_KEY_ENV_VAR. Codex sets these through
     [shell_environment_policy.set] in config.toml. CI and eval harnesses can set them too.
  2. The values the harness wrote into SKILL.md, passed as --live and --key-var.
     A value that still reads ${...} was not filled in by this harness and is ignored.
  3. Defaults: live testing off, key variable TYPESAFE_API_KEY.

The hook cannot read SKILL.md placeholders, so step 2 comes from where each harness
keeps the settings instead: Claude Code exports plugin options to hooks as
CLAUDE_PLUGIN_OPTION_LIVE_TESTING and CLAUDE_PLUGIN_OPTION_KEY_ENV_VAR. Codex does not
pass [shell_environment_policy.set] to hooks, so the hook reads config.toml itself.

Examples:
  python3 jev_live.py status --live '${user_config.live_testing}' --live '${JEV_LIVE_TESTING}'
  python3 jev_live.py exec --key-var MY_KEY -- uv run --with typesafe-sdk python probe.py
  python3 jev_live.py hook --harness codex
"""

import argparse
import fnmatch
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_KEY_VAR = "TYPESAFE_API_KEY"
DEFAULT_BASE_URL = "https://api.typesafe.ai"
VAR_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def filled(values):
    """The first value the harness actually substituted, or None."""
    for value in values or []:
        value = value.strip()
        if value and "${" not in value:
            return value
    return None


def resolve(env_name, passed, default):
    if os.environ.get(env_name, "").strip():
        return os.environ[env_name].strip(), f"environment variable {env_name}"
    value = filled(passed)
    if value is not None:
        return value, "plugin setting"
    return default, "default"


def codex_config():
    """(config.toml as a dict, None) or ({}, a reason it could not be read)."""
    home = os.environ.get("CODEX_HOME", "").strip()
    path = (Path(home).expanduser() if home else Path.home() / ".codex") / "config.toml"
    if not path.exists():
        return {}, None
    try:
        import tomllib
    except ModuleNotFoundError:
        return {}, f"could not read {path}: needs Python 3.11 or later"
    try:
        return tomllib.loads(path.read_text(encoding="utf-8-sig")), None
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return {}, f"could not read {path}: {exc}"


def codex_filters(policy, key_var):
    """Why the agent's shell may not see the key even though this hook does."""
    notes = []
    include_only = policy.get("include_only")
    if include_only and not any(fnmatch.fnmatchcase(key_var, pattern) for pattern in include_only):
        notes.append(f"shell_environment_policy.include_only may not let {key_var} through")
    if policy.get("ignore_default_excludes") is False:
        notes.append(f"ignore_default_excludes = false drops {key_var} from the agent's shell")
    if policy.get("inherit") in ("none", "core") and key_var not in policy.get("set", {}):
        notes.append(f"inherit = \"{policy['inherit']}\" keeps {key_var} out of the agent's shell")
    return notes


def hook(args):
    try:
        lines = hook_lines(args.harness)
    except Exception as exc:  # A session must start even if this breaks.
        lines = [f"could not check the settings: {exc}"]
    print("building-with-typesafe-jev live-testing settings at session start:")
    for line in lines:
        print(f"- {line}")
    print("Run the skill's status check before the first live call; settings change only between sessions.")
    return 0


def hook_lines(harness):
    lines, notes, saved, policy = [], [], {}, {}
    if harness == "claude":
        saved = {"JEV_LIVE_TESTING": os.environ.get("CLAUDE_PLUGIN_OPTION_LIVE_TESTING", ""),
                 "JEV_KEY_ENV_VAR": os.environ.get("CLAUDE_PLUGIN_OPTION_KEY_ENV_VAR", "")}
    else:
        config, problem = codex_config()
        policy = config.get("shell_environment_policy", {})
        saved = policy.get("set", {})
        if problem:
            notes.append(problem)
    live, live_from = resolve("JEV_LIVE_TESTING", [str(saved.get("JEV_LIVE_TESTING", ""))], "off")
    key_var, key_var_from = resolve("JEV_KEY_ENV_VAR", [str(saved.get("JEV_KEY_ENV_VAR", ""))], DEFAULT_KEY_VAR)
    if harness == "codex":
        live_from, key_var_from = (f.replace("plugin setting", "Codex config.toml") for f in (live_from, key_var_from))
    live_on = live.lower() == "on"
    lines.append(f"live testing: {'on' if live_on else 'off'} (from {live_from})")
    if not VAR_NAME.match(key_var):
        lines.append(f"key variable: invalid name {key_var!r} (from {key_var_from})")
        return lines + notes + ["ready: no"]
    lines.append(f"key variable: {key_var} (from {key_var_from})")
    present = bool(os.environ.get(key_var) or str(policy.get("set", {}).get(key_var, "")))
    lines.append(f"key: {'set' if present else 'not set'}")
    if harness == "codex" and present:
        notes += codex_filters(policy, key_var)
    return lines + notes + [f"ready: {'yes' if live_on and present else 'no'}"]


def status(args):
    live, live_from = resolve("JEV_LIVE_TESTING", args.live, "off")
    key_var, key_var_from = resolve("JEV_KEY_ENV_VAR", args.key_var, DEFAULT_KEY_VAR)
    live_on = live.lower() == "on"
    print(f"live testing: {'on' if live_on else 'off'} (from {live_from})")
    if not VAR_NAME.match(key_var):
        print(f"key variable: invalid name {key_var!r} (from {key_var_from})")
        print("ready: no")
        return 0
    print(f"key variable: {key_var} (from {key_var_from})")
    value = os.environ.get(key_var, "")
    print(f"key: set, {len(value)} characters" if value else "key: not set in this shell")
    base_url = os.environ.get("TYPESAFE_BASE_URL", "").strip()
    if base_url and base_url.rstrip("/") != DEFAULT_BASE_URL:
        print(f"base url: {base_url} (the key must belong to this endpoint)")
    print(f"ready: {'yes' if live_on and value else 'no'}")
    return 0


def run(args):
    key_var = args.key_var
    if not VAR_NAME.match(key_var):
        print(f"jev_live: invalid variable name {key_var!r}", file=sys.stderr)
        return 2
    value = os.environ.get(key_var, "")
    if not value:
        # Never fall back to another variable: it may hold a different account's key.
        print(f"jev_live: {key_var} is not set in this shell", file=sys.stderr)
        return 2
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        print("jev_live: no command given after --", file=sys.stderr)
        return 2
    # Resolve the program first so Windows can run .cmd launchers such as npx.
    program = shutil.which(command[0])
    if program is None:
        print(f"jev_live: command not found: {command[0]}", file=sys.stderr)
        return 127
    env = dict(os.environ)
    env["TYPESAFE_API_KEY"] = value
    try:
        return subprocess.run([program, *command[1:]], env=env).returncode
    except KeyboardInterrupt:
        return 130


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="action", required=True)

    p = sub.add_parser("status", help="show the resolved settings and whether the key is set")
    p.add_argument("--live", action="append", help="live-testing value from the harness (repeatable)")
    p.add_argument("--key-var", action="append", help="key variable name from the harness (repeatable)")
    p.set_defaults(func=status)

    p = sub.add_parser("exec", help="run a command with TYPESAFE_API_KEY set from --key-var")
    p.add_argument("--key-var", default=DEFAULT_KEY_VAR, help="variable that holds the key")
    p.add_argument("command", nargs=argparse.REMAINDER, help="-- then the command to run")
    p.set_defaults(func=run)

    p = sub.add_parser("hook", help="SessionStart hook: print the settings for the agent's context")
    p.add_argument("--harness", choices=["claude", "codex"], required=True, help="where to find the saved settings")
    p.set_defaults(func=hook)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
