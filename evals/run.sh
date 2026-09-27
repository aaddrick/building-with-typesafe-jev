#!/usr/bin/env bash
# Run the eval suite twice per case: once with this plugin loaded, once without.
# Extra arguments pass through to `claude plugin eval`, e.g. --runs 1 or --case triage-ticket.
set -euo pipefail
cd "$(dirname "$0")/.."

# No TypeSafe key is passed to a run. The container also keeps your home out
# of reach. Use evals/container/run.sh for scores you keep.

source evals/lib/provenance.sh
results=$(new_results_dir host)
record_start

status=0
claude plugin eval . \
  --trust-plugin \
  --output-dir "$results" \
  --scaffold \
  --keep-temp \
  --model "${EVAL_MODEL:-claude-sonnet-5}" \
  --judge-model "${EVAL_JUDGE_MODEL:-claude-opus-5-5}" \
  --allow-tools Bash Write Edit WebSearch WebFetch \
    "WebFetch(domain:api.typesafe.ai)" "WebFetch(domain:docs.typesafe.ai)" \
    "WebFetch(domain:pypi.org)" "WebFetch(domain:files.pythonhosted.org)" \
  --threshold 0 \
  --no-publish \
  --max-cost-usd "${EVAL_MAX_COST_USD:-60}" \
  "$@" || status=$?
record_finish "$results"
exit $status
