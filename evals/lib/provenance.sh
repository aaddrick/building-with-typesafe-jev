# Sourced by evals/run.sh and evals/container/run.sh. Records the commit the
# suite ran from, and any uncommitted changes to files that shape a run, as
# provenance.json in the run's own results directory. Each run script names that
# directory itself, so runs started side by side never record into each other's.
# Call new_results_dir, then record_start before the run and record_finish after it.

# Create and print a results directory for this run: evals/results/<UTC time>-<label>.
# mkdir without -p fails rather than share a directory with a run started the same second.
# EVAL_BATCH, set by EVAL_PLUGIN=all, gives the three arms of one eval batch one stamp.
new_results_dir() {
  local dir=evals/results/${EVAL_BATCH:-$(date -u +%Y-%m-%dT%H-%M-%SZ)}-$1
  mkdir -p evals/results
  mkdir "$dir" && echo "$dir"
}
record_start() {
  prov_commit=$(git rev-parse HEAD)
  prov_dirty=$(git status --porcelain -- skills evals .claude-plugin | grep -vE ' evals/(results/|runs/|LEDGER.md|README.md|docs/)' || true)
}
# The run asks for a model by name; each trace records the model that answered.
# record_finish counts those, so the record shows what a name resolved to.
# It also scrubs the kept run directories, so traces can stay: the Claude login
# token, and anything shaped like an Anthropic key, become [REDACTED].
record_finish() {
  local dir=$1
  PROV_DIRTY="$prov_dirty" python3 - "$dir" "$prov_commit" <<'PY'
import collections, json, os, sys
out, commit = sys.argv[1], sys.argv[2]
record = {"commit": commit, "batch": os.environ.get("EVAL_BATCH", ""),
          "dirty": [l[3:] for l in os.environ["PROV_DIRTY"].splitlines() if l.strip()]}
if os.environ.get("EVAL_PLUGIN") == "official":
    record["official_ref"] = os.environ.get("EVAL_OFFICIAL_REF", "")
if os.environ.get("EVAL_PLUGIN") == "this":
    record["this_ref"] = os.environ.get("EVAL_THIS_REF", "")
import re
secret = re.compile("|".join(filter(None, [
    re.escape(os.environ["CLAUDE_CODE_OAUTH_TOKEN"]) if os.environ.get("CLAUDE_CODE_OAUTH_TOKEN") else "",
    r"sk-ant-[A-Za-z0-9_\-]{20,}"])))
models, skills, unread, scrubbed = collections.Counter(), collections.Counter(), 0, 0
try:
    result = json.load(open(os.path.join(out, "aggregate-result.json")))
    traces = [r.get("tracePath") for c in result["cases"] for a in c["arms"].values() for r in a]
except (OSError, ValueError, KeyError):
    traces = []
for path in filter(None, traces):
    # The container writes /out/...; that is the repo root on the host.
    path = path.replace("/out/", "./", 1) if path.startswith("/out/") else path
    # A trace sits at <kept dir>/out/trace.jsonl. Scrub every file there that
    # can be read; the harness seals home/ and tmp/ (mode 000), which stay shut.
    for root, _, files in os.walk(os.path.dirname(os.path.dirname(path))):
        for name in files:
            f = os.path.join(root, name)
            try:
                text = open(f, encoding="utf-8").read()
            except (OSError, UnicodeDecodeError):
                continue
            clean, n = secret.subn("[REDACTED]", text)
            if n:
                try:
                    # The harness leaves kept files read-only.
                    os.chmod(f, os.stat(f).st_mode | 0o200)
                    open(f, "w", encoding="utf-8").write(clean)
                    scrubbed += n
                except OSError:
                    print(f"Could not scrub {f}; delete it before sharing", file=sys.stderr)
    seen, loaded = set(), set()
    try:
        for line in open(path):
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if not isinstance(event, dict):
                continue
            # A permission_denied event carries its message as a string.
            message = event.get("message")
            message = message if isinstance(message, dict) else {}
            model = event.get("model") if event.get("subtype") == "init" else None
            model = model or message.get("model")
            if model:
                seen.add(model)
            for part in message.get("content") or []:
                if isinstance(part, dict) and part.get("type") == "tool_use" and part.get("name") == "Skill":
                    loaded.add(str((part.get("input") or {}).get("skill", "?")))
    except OSError:
        unread += 1
        continue
    models.update(seen)
    skills.update(loaded)
# Each count is a number of runs: how many named that model, how many loaded that skill.
record["runs"] = len([t for t in traces if t])
record["agent_models"] = dict(models)
record["skills_loaded"] = dict(skills)
if unread:
    record["traces_unread"] = unread
if scrubbed:
    record["secrets_redacted"] = scrubbed
    print(f"Redacted {scrubbed} secret(s) from the kept traces", file=sys.stderr)
json.dump(record, open(os.path.join(out, "provenance.json"), "w"), indent=1)
PY
  # Token counts leave the traces here, since the traces stay out of git.
  python3 evals/lib/usage.py "$dir" || echo "Could not record token usage for $dir" >&2
  echo "Provenance: ${prov_commit:0:7}${prov_dirty:+ (uncommitted changes, see provenance.json)} -> $dir"
}
