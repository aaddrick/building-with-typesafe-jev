#!/usr/bin/env bash
# Run the eval suite inside a rootless podman container. The repo is mounted
# read-only; only evals/results is writable. Arguments pass through to
# `claude plugin eval`, e.g. --case triage-ticket --runs 1.
set -euo pipefail
cd "$(dirname "$0")/../.."
image=typesafe-jev-evals

# `all` builds once and passes EVAL_SKIP_BUILD to the two runs it starts.
[ -n "${EVAL_SKIP_BUILD:-}" ] || podman build -q -t "$image" -f evals/container/Containerfile evals/container >/dev/null

# Authenticate with CLAUDE_CODE_OAUTH_TOKEN if it is set (a long-lived token from
# `claude setup-token`). Otherwise pass the host's current OAuth access token
# only: without the refresh token the container cannot rotate the host's login,
# so that token must outlive the run.
if [ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]; then
  creds=~/.claude/.credentials.json
  min_left=$(python3 -c "import json,time;print(int((json.load(open('$creds'))['claudeAiOauth']['expiresAt']/1000-time.time())/60))")
  if [ "$min_left" -lt "${EVAL_MIN_TOKEN_MINUTES:-50}" ]; then
    echo "The Claude login token expires in $min_left min. Set CLAUDE_CODE_OAUTH_TOKEN from 'claude setup-token', or retry after the host refreshes its login." >&2
    exit 1
  fi
  CLAUDE_CODE_OAUTH_TOKEN=$(python3 -c "import json;print(json.load(open('$creds'))['claudeAiOauth']['accessToken'])")
fi
export CLAUDE_CODE_OAUTH_TOKEN

# The official plugin's commit. Move it forward on purpose, and note it in the
# ledger, so a change in its score is never a silent plugin update.
export EVAL_OFFICIAL_REF=${EVAL_OFFICIAL_REF:-65a39f393687675ce170e6094757de20370365b9}

# This plugin installs from GitHub at the commit checked out here, the way a
# user installs it. So that commit must be pushed, and nothing outside evals/
# may differ from it: the run would test GitHub's copy, not yours. The cases
# still come from this checkout, so provenance.json records any change to them.
: "${EVAL_PLUGIN:=this}"
if [ -z "${EVAL_SKIP_BUILD:-}" ] && { [ "$EVAL_PLUGIN" = this ] || [ "$EVAL_PLUGIN" = all ]; }; then
  export EVAL_THIS_REF=$(git rev-parse HEAD)
  if [ -n "$(git status --porcelain -- . ':!evals')" ]; then
    echo "Uncommitted changes outside evals/; commit and push before testing this plugin:" >&2
    git status --short -- . ':!evals' >&2
    exit 1
  fi
  git fetch -q origin
  if [ -z "$(git branch -r --contains "$EVAL_THIS_REF")" ]; then
    echo "Commit ${EVAL_THIS_REF:0:7} is not on GitHub yet; push it before testing this plugin." >&2
    exit 1
  fi
fi

case "${EVAL_PLUGIN:=this}" in
this|official|none) ;;
all)
  # All three arms in one eval batch, one container each, started together so
  # they share a time window and the same live docs. The results directories
  # carry one batch stamp, and each run keeps its own cost ceiling.
  # Arguments go to all three, so -j is per arm: -j 4 runs 12 at once.
  export EVAL_BATCH=$(date -u +%Y-%m-%dT%H-%M-%SZ) EVAL_SKIP_BUILD=1
  pids=()
  for arm in none this official; do
    # Process substitution, not a pipe, so wait sees each run's own status.
    EVAL_PLUGIN=$arm "$0" "$@" > >(sed -u "s/^/[$arm] /") 2>&1 &
    pids+=($!)
  done
  status=0
  for pid in "${pids[@]}"; do wait "$pid" || status=1; done
  echo "Eval batch $EVAL_BATCH: evals/results/$EVAL_BATCH-{none,this,official}"
  echo "Compare: python3 evals/lib/compare.py $EVAL_BATCH"
  exit $status ;;
*) echo "EVAL_PLUGIN must be 'this', 'official', 'none', or 'all'" >&2; exit 2 ;;
esac

source evals/lib/provenance.sh
results=$(new_results_dir "$EVAL_PLUGIN")
# The container writes to the directory named here, so provenance lands with its run.
export EVAL_OUT_NAME=${results#evals/results/}
record_start

status=0
# unmask=/proc/* lets Claude Code's bubblewrap sandbox mount /proc for each Bash call.
podman run --rm --userns=keep-id --security-opt label=disable --security-opt 'unmask=/proc/*' \
  -v "$PWD:/src:ro" \
  -v "$PWD/evals/results:/out/evals/results" \
  --env CLAUDE_CODE_OAUTH_TOKEN \
  --env EVAL_MODEL --env EVAL_JUDGE_MODEL --env EVAL_MAX_COST_USD --env EVAL_PLUGIN --env EVAL_OFFICIAL_REF --env EVAL_THIS_REF --env EVAL_OUT_NAME \
  "$image" "$@" || status=$?
record_finish "$results"
exit $status
