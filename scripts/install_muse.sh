#!/usr/bin/env bash
# Install the skill into Muse (muse.ai), Meta's personal agent.
#
# Muse loads skills from ~/workspace/skills/<folder>/SKILL.md on its own
# computer. It reads a narrower frontmatter than Claude Code or Codex: the
# name must use underscores, and both values must be one-line quoted strings.
# This script copies the skill folder there and rewrites the frontmatter into
# that shape. The rest of the folder is copied unchanged.
#
# Run it inside Muse's computer (ask Muse to run the command in the README):
#
#   curl -fsSL https://raw.githubusercontent.com/aaddrick/building-with-typesafe-jev/main/scripts/install_muse.sh | bash
#
# Environment:
#   MUSE_SKILLS_DIR     where Muse reads skills (default: ~/workspace/skills)
#   MUSE_SKILL_SOURCE   a local skills/building-with-typesafe-jev folder to
#                       install instead of downloading the latest release
#
# Run it again to update. It replaces the installed copy.

set -euo pipefail

SKILL=building-with-typesafe-jev
REPO=aaddrick/building-with-typesafe-jev
DEST_ROOT="${MUSE_SKILLS_DIR:-$HOME/workspace/skills}"
DEST="$DEST_ROOT/$SKILL"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

if [ -n "${MUSE_SKILL_SOURCE:-}" ]; then
  src="$MUSE_SKILL_SOURCE"
else
  curl -fsSL "https://codeload.github.com/$REPO/tar.gz/refs/heads/main" | tar -xz -C "$work"
  src="$work/${REPO#*/}-main/skills/$SKILL"
fi

if [ ! -f "$src/SKILL.md" ]; then
  echo "error: no SKILL.md in $src" >&2
  exit 1
fi

stage="$work/stage/$SKILL"
mkdir -p "$(dirname "$stage")"
cp -R "$src" "$stage"
rm -rf "$stage/__pycache__"

# Rewrite the frontmatter. Keep the description, drop every other key, and
# quote both values. The body below the closing --- is copied as is.
skill_md="$stage/SKILL.md"
if [ "$(head -n 1 "$skill_md")" != "---" ]; then
  echo "error: $skill_md has no frontmatter" >&2
  exit 1
fi
end="$(awk 'NR > 1 && $0 == "---" { print NR; exit }' "$skill_md")"
if [ -z "$end" ]; then
  echo "error: $skill_md frontmatter never closes" >&2
  exit 1
fi
desc="$(sed -n "2,$((end - 1))p" "$skill_md" | sed -n 's/^description:[[:space:]]*//p')"
if [ -z "$desc" ]; then
  echo "error: $skill_md has no one-line description" >&2
  exit 1
fi
desc="${desc//\\/\\\\}"
desc="${desc//\"/\\\"}"
name="${SKILL//-/_}"

{
  printf -- '---\nname: "%s"\ndescription: "%s"\n---\n' "$name" "$desc"
  tail -n "+$((end + 1))" "$skill_md"
} > "$work/SKILL.md"
mv "$work/SKILL.md" "$skill_md"

mkdir -p "$DEST_ROOT"
rm -rf "$DEST"
mv "$stage" "$DEST"

echo "Installed $name into $DEST"
echo "Start a new Muse chat so it picks up the skill."
