#!/usr/bin/env bash
# Runs inside the container. Installs a plugin the way a user would, then runs
# the suite with it loaded. No TypeSafe key enters the container, so live
# testing stays off and the agents design from the docs alone.
# EVAL_PLUGIN picks the plugin: `this` (default) for this repo's plugin,
# `official` for TypeSafe's typesafe@typesafe-ai, or `none` for no plugin. Each
# is one arm; evals/container/run.sh with EVAL_PLUGIN=all runs the three together.
# Arguments pass through to `claude plugin eval`.
set -euo pipefail
: "${CLAUDE_CODE_OAUTH_TOKEN:?missing; start the container with evals/container/run.sh}"
: "${EVAL_OUT_NAME:?missing; start the container with evals/container/run.sh}"

# Both plugins come from GitHub at an exact commit. `marketplace add owner/repo#ref`
# takes only a branch or tag, so clone over HTTPS, check out the commit, and
# add the checkout as a local marketplace. The clone holds that commit's files
# and nothing from this machine.
from_github() {
  local repo=$1 ref=$2 dir=/tmp/marketplaces/${1//\//-}
  git clone -q "https://github.com/$repo.git" "$dir"
  git -C "$dir" checkout -q "$ref"
  claude plugin marketplace add "$dir" >/dev/null
}

# Claude Code asks to confirm first use in a directory; the container is new every time.
printf '{"hasCompletedOnboarding":true}\n' > ~/.claude.json

cd /out
# Kept run directories land under evals/results/tmp on the host, so traces outlive the container.
export TMPDIR=/out/evals/results/tmp
mkdir -p "$TMPDIR"

common=(
  --scaffold
  --keep-temp
  --model "${EVAL_MODEL:-claude-sonnet-5}"
  --judge-model "${EVAL_JUDGE_MODEL:-claude-opus-5-5}"
  --allow-tools Bash Write Edit WebSearch WebFetch
    "WebFetch(domain:api.typesafe.ai)" "WebFetch(domain:docs.typesafe.ai)"
    "WebFetch(domain:pypi.org)" "WebFetch(domain:files.pythonhosted.org)"
  --threshold 0
  --no-publish
  --max-cost-usd "${EVAL_MAX_COST_USD:-60}"
)

# Stage the cases from the read-only repo without results, kept runs, or git.
stage=/tmp/stage
mkdir -p "$stage"
tar -C /src --exclude=./.git --exclude=./evals/results --exclude=./evals/runs -cf - . | tar -C "$stage" -xf -

case "${EVAL_PLUGIN:-this}" in
this)
  # This plugin, installed from GitHub the way a user installs it, at the commit
  # run.sh checked is pushed.
  from_github aaddrick/building-with-typesafe-jev "${EVAL_THIS_REF:?}"
  claude plugin install building-with-typesafe-jev@building-with-typesafe-jev >/dev/null
  installed=$(ls -d ~/.claude/plugins/cache/building-with-typesafe-jev/building-with-typesafe-jev/*/ | tail -1)
  label=this
  ;;
official)
  # TypeSafe's own plugin, installed from its GitHub marketplace at a pinned
  # commit, so two official runs test the same plugin.
  from_github typesafe-ai/skills "${EVAL_OFFICIAL_REF:?}"
  claude plugin install typesafe@typesafe-ai >/dev/null
  installed=$(ls -d ~/.claude/plugins/cache/typesafe-ai/typesafe/*/ | tail -1)
  label=official
  ;;
none)
  # No plugin: the target holds only the cases. The harness still resolves a
  # directory as a plugin, so this arm loads an empty one.
  label=none
  ;;
*)
  echo "EVAL_PLUGIN must be 'this', 'official', or 'none'" >&2; exit 2 ;;
esac

# The installed copy keeps no eval cases, so nothing on disk pairs them with
# the skill. The suite runs against a separate copy of the installed plugin with
# the cases added; the harness blocks reads of that copy's eval directory.
work=/tmp/plugin-under-test
mkdir -p "$work"
if [ "$label" != none ]; then
  rm -rf "$installed/evals"
  cp -r "$installed/." "$work"
fi
cp -r "$stage/evals" "$work/evals"

# run.sh created this directory on the host and records provenance in it.
out=/out/evals/results/$EVAL_OUT_NAME
if [ "$label" = none ]; then
  echo "Plugin under test: none (baseline only)"
else
  cp "$work/.claude-plugin/plugin.json" "$out/plugin-under-test.json"
  echo "Plugin under test: $(python3 -c "import json;d=json.load(open('$out/plugin-under-test.json'));print(d['name'], d.get('version',''))")"
fi
if [ "$label" = official ]; then
  git -C /tmp/marketplaces/typesafe-ai-skills rev-parse HEAD > "$out/official-commit.txt"
fi

# Every plugin runs the same way: one arm, --ablation none, with its plugin
# directory loaded. For `none` that directory holds only the cases, so no
# skills, commands, hooks, or servers load. The three arms of an eval batch differ
# only in the plugin.
exec claude plugin eval "$work" --trust-plugin --ablation none --output-dir "$out" "${common[@]}" "$@"
