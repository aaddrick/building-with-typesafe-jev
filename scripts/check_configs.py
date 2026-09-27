#!/usr/bin/env python3
"""Check every shipped manifest and the skill itself. Exit 1 on any failure.

- Every JSON manifest parses, and the three plugin manifests agree on name and version.
- Each SKILL.md has frontmatter with `name` and `description` (plus the Claude Code
  invocation keys for jev-settings), and the name matches its folder.
- Every relative file the skill names (`api-reference.md`, `prior-art/INDEX.md`, ...) exists.
- Live testing ships off: the Claude Code userConfig declares the two settings with safe
  defaults, and every SKILL.md that runs the status script passes the placeholders that
  manifest fills in, plus the environment variables Codex and Antigravity CLI read. Every script a skill names exists and compiles.
- No file in the repo contains something shaped like a TypeSafe API key.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "building-with-typesafe-jev"
SETTINGS_DIR = ROOT / "skills" / "jev-settings"
# Extra frontmatter keys each skill may carry, beyond name and description.
EXTRA_KEYS = {SKILL_DIR.name: [], SETTINGS_DIR.name: ["disable-model-invocation", "argument-hint"]}
PLACEHOLDERS = ["${user_config.live_testing}", "${JEV_LIVE_TESTING}",
                "${user_config.key_env_var}", "${JEV_KEY_ENV_VAR}"]
SCRIPT_REF = re.compile(r"scripts/([\w-]+\.py)")
MANIFESTS = [
    ROOT / ".claude-plugin" / "plugin.json",
    ROOT / ".claude-plugin" / "marketplace.json",
    ROOT / ".codex-plugin" / "plugin.json",
    ROOT / "plugin.json",
]
KEY_SHAPE = re.compile(r"apikey_[0-9a-f]{20,}")
SKILL_REF = re.compile(r"`((?:prior-art/)?[\w.-]+\.md)`")

errors: list[str] = []

parsed = {}
for path in MANIFESTS:
    try:
        parsed[path] = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path.relative_to(ROOT)}: {exc}")

plugins = [parsed.get(p) for p in (MANIFESTS[0], MANIFESTS[2], MANIFESTS[3])]
if all(plugins):
    if len({p["name"] for p in plugins}) != 1:
        errors.append("plugin manifests disagree on name")
    if len({p["version"] for p in plugins}) != 1:
        errors.append("plugin manifests disagree on version")

for skill_dir, extra in EXTRA_KEYS.items():
    path = ROOT / "skills" / skill_dir / "SKILL.md"
    skill = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", skill, re.S)
    if not match:
        errors.append(f"{skill_dir}/SKILL.md: no frontmatter")
        continue
    keys = [line.split(":", 1)[0] for line in match.group(1).splitlines() if re.match(r"^\w", line)]
    if keys[:2] != ["name", "description"] or sorted(keys[2:]) != sorted(extra):
        errors.append(f"{skill_dir}/SKILL.md: frontmatter keys must be name, description{''.join(', ' + k for k in extra)}; found {keys}")
    name = re.search(r"^name:\s*(.+)$", match.group(1), re.M)
    if not name or name.group(1).strip() != skill_dir:
        errors.append(f"{skill_dir}/SKILL.md: name does not match its folder")
    if len(match.group(1)) > 1024:
        errors.append(f"{skill_dir}/SKILL.md: frontmatter is over 1024 characters")
    if "jev_live.py status" in skill:
        for placeholder in PLACEHOLDERS:
            if placeholder not in skill:
                errors.append(f"{skill_dir}/SKILL.md: runs the status script without {placeholder}")
    for script in set(SCRIPT_REF.findall(skill)):
        if not any((ROOT / "skills" / d / "scripts" / script).exists() for d in EXTRA_KEYS):
            errors.append(f"{skill_dir}/SKILL.md: names scripts/{script}, which does not exist")

for script in ROOT.glob("skills/*/scripts/*.py"):
    try:
        compile(script.read_text(encoding="utf-8"), str(script), "exec")
    except SyntaxError as exc:
        errors.append(f"{script.relative_to(ROOT)}: does not compile ({exc})")

claude_manifest = parsed.get(MANIFESTS[0]) or {}
user_config = claude_manifest.get("userConfig", {})
live = user_config.get("live_testing", {})
if live.get("default") != "off" or sorted(live.get("options", [])) != ["off", "on"]:
    errors.append(".claude-plugin/plugin.json: userConfig.live_testing must offer on/off and default to off")
if user_config.get("key_env_var", {}).get("default") != "TYPESAFE_API_KEY":
    errors.append(".claude-plugin/plugin.json: userConfig.key_env_var must default to TYPESAFE_API_KEY")
for option in user_config.values():
    if option.get("sensitive"):
        errors.append(".claude-plugin/plugin.json: a sensitive userConfig value is never filled into SKILL.md")

for md in SKILL_DIR.rglob("*.md"):
    for ref in SKILL_REF.findall(md.read_text(encoding="utf-8")):
        base = SKILL_DIR if ref.startswith("prior-art/") or md.parent == SKILL_DIR else md.parent
        if not (base / ref).exists() and not (SKILL_DIR / ref).exists() and not (SKILL_DIR / "prior-art" / ref).exists():
            errors.append(f"{md.relative_to(ROOT)}: names `{ref}`, which does not exist")

for path in ROOT.rglob("*"):
    if path.is_file() and ".git" not in path.parts and path.suffix in {".md", ".json", ".py", ".yaml", ".yml", ".txt", ".toml", ".sh"}:
        if KEY_SHAPE.search(path.read_text(encoding="utf-8", errors="ignore")):
            errors.append(f"{path.relative_to(ROOT)}: contains something shaped like an API key")

for e in errors:
    print(f"error: {e}")
print("ok" if not errors else f"{len(errors)} error(s)")
sys.exit(1 if errors else 0)
