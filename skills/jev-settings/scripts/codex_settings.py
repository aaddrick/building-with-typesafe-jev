#!/usr/bin/env python3
"""Read or change the building-with-typesafe-jev settings in Codex's config.toml.

Codex has no per-plugin settings, so the two settings live in
[shell_environment_policy.set], which Codex adds to the environment of every
shell command the agent runs:

  [shell_environment_policy.set]
  JEV_LIVE_TESTING = "on"
  JEV_KEY_ENV_VAR = "TYPESAFE_API_KEY"

The file is edited as text so the user's comments and layout survive, then
parsed again. Nothing is written unless the only change is the requested one.
Standard library only; needs Python 3.11 or later for tomllib.

  python3 codex_settings.py show
  python3 codex_settings.py set --live on --key-var TYPESAFE_API_KEY
"""

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    sys.exit("codex_settings: needs Python 3.11 or later (tomllib)")

LIVE = "JEV_LIVE_TESTING"
KEY_VAR = "JEV_KEY_ENV_VAR"
VAR_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SET_HEADER = re.compile(r"^[ \t]*\[[ \t]*shell_environment_policy[ \t]*\.[ \t]*set[ \t]*\][ \t]*(#[^\r\n]*)?\r?$", re.M)
ANY_HEADER = re.compile(r"^[ \t]*\[", re.M)


def config_path() -> Path:
    home = os.environ.get("CODEX_HOME", "").strip()
    return (Path(home).expanduser() if home else Path.home() / ".codex") / "config.toml"


def manual(path: Path, values: dict) -> str:
    lines = "\n".join(f'{k} = "{v}"' for k, v in values.items())
    return (f"Add these lines to {path} yourself, under [shell_environment_policy.set]:\n\n"
            f"[shell_environment_policy.set]\n{lines}\n")


def edit(text: str, values: dict, nl: str) -> str:
    """Return text with the keys set under [shell_environment_policy.set]."""
    header = SET_HEADER.search(text)
    if header is None:
        block = "[shell_environment_policy.set]" + nl + "".join(f'{k} = "{v}"{nl}' for k, v in values.items())
        if text and not text.endswith(("\n", "\r\n")):
            text += nl
        return text + (nl if text else "") + block
    start = header.end() - (1 if header.group(0).endswith("\r") else 0)  # keep a CRLF pair whole
    following = ANY_HEADER.search(text, start + 1)
    end = following.start() if following else len(text)
    section = text[start:end]
    inserts = ""
    for key, value in values.items():
        line = re.compile(rf"^([ \t]*){key}[ \t]*=[^\r\n]*", re.M)
        if line.search(section):
            section = line.sub(lambda m: f'{m.group(1)}{key} = "{value}"', section, count=1)
        else:
            inserts += f'{key} = "{value}"{nl}'
    if inserts:
        section = nl + inserts.rstrip("\r\n") + section if section.startswith(("\n", "\r\n")) else nl + inserts + section
    return text[:start] + section + text[end:]


def without_ours(data: dict) -> dict:
    policy = dict(data.get("shell_environment_policy", {}))
    if "set" in policy:
        policy["set"] = {k: v for k, v in policy["set"].items() if k not in (LIVE, KEY_VAR)}
        if not policy["set"]:
            del policy["set"]
    out = dict(data)
    if policy:
        out["shell_environment_policy"] = policy
    else:
        out.pop("shell_environment_policy", None)
    return out


def warnings(data: dict) -> list[str]:
    policy = data.get("shell_environment_policy", {})
    notes = []
    if policy.get("include_only"):
        notes.append(f"include_only is set: it must let {LIVE}, {KEY_VAR}, and your key variable through.")
    if policy.get("ignore_default_excludes") is False:
        notes.append("ignore_default_excludes = false: Codex drops variables with KEY, SECRET, or TOKEN "
                     "in their names, so the agent cannot see your key variable.")
    if policy.get("inherit") in ("none", "core"):
        notes.append(f"inherit = \"{policy['inherit']}\": your key variable does not reach the agent's shell "
                     "unless you add it to [shell_environment_policy.set] yourself.")
    return notes


def show(_args) -> int:
    path = config_path()
    data = {}
    if path.exists():
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8-sig"))
        except tomllib.TOMLDecodeError as exc:
            print(f"{path}: not valid TOML ({exc})")
            return 1
    saved = data.get("shell_environment_policy", {}).get("set", {})
    print(f"file: {path}{'' if path.exists() else ' (does not exist yet)'}")
    for key, default in ((LIVE, "off"), (KEY_VAR, "TYPESAFE_API_KEY")):
        print(f"saved {key}: {saved.get(key, f'not set (default {default})')}")
        print(f"this session's {key}: {os.environ.get(key) or 'not set'}")
    for note in warnings(data):
        print(f"note: {note}")
    return 0


def set_values(args) -> int:
    values = {}
    if args.live is not None:
        values[LIVE] = args.live
    if args.key_var is not None:
        if not VAR_NAME.match(args.key_var):
            print(f"codex_settings: {args.key_var!r} is not a valid environment variable name", file=sys.stderr)
            return 2
        values[KEY_VAR] = args.key_var
    if not values:
        print("codex_settings: give --live, --key-var, or both", file=sys.stderr)
        return 2

    path = config_path()
    raw = path.read_bytes() if path.exists() else b""
    text = raw.decode("utf-8-sig")
    bom = raw.startswith(b"\xef\xbb\xbf")
    nl = "\r\n" if "\r\n" in text else "\n"
    try:
        before = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        print(f"codex_settings: {path} is not valid TOML ({exc}). Nothing changed.", file=sys.stderr)
        return 1

    policy = before.get("shell_environment_policy", {})
    if "set" in policy and not SET_HEADER.search(text):
        # An inline table or dotted keys: editing those as text is not safe.
        print(f"codex_settings: {path} defines shell_environment_policy.set in a form this script does not edit.",
              file=sys.stderr)
        print(manual(path, values), file=sys.stderr)
        return 1

    new_text = edit(text, values, nl)
    try:
        after = tomllib.loads(new_text)
        ok = all(after["shell_environment_policy"]["set"].get(k) == v for k, v in values.items())
        ok = ok and without_ours(after) == without_ours(before)
    except (tomllib.TOMLDecodeError, KeyError, TypeError):
        ok = False
    if not ok:
        print("codex_settings: could not make the change safely. Nothing changed.", file=sys.stderr)
        print(manual(path, values), file=sys.stderr)
        return 1

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".config.toml.")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write((b"\xef\xbb\xbf" if bom else b"") + new_text.encode("utf-8"))
        if path.exists():
            os.chmod(tmp, path.stat().st_mode & 0o777)
        os.replace(tmp, path)
    except OSError as exc:
        Path(tmp).unlink(missing_ok=True)
        print(f"codex_settings: could not write {path} ({exc}). Nothing changed.", file=sys.stderr)
        print(manual(path, values), file=sys.stderr)
        return 1

    print(f"updated {path}:")
    for key, value in values.items():
        print(f'  {key} = "{value}"')
    for note in warnings(after):
        print(f"note: {note}")
    print("Start a new Codex session for the change to take effect.")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("show", help="print the saved settings and what this session sees").set_defaults(func=show)
    p = sub.add_parser("set", help="save one or both settings")
    p.add_argument("--live", choices=["on", "off"])
    p.add_argument("--key-var", help="name of the variable that holds the key (never the key itself)")
    p.set_defaults(func=set_values)
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
