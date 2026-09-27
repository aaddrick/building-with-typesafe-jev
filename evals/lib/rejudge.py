"""Re-judge kept runs' llm checks with judges from other providers.

The published score is a panel of three judges from three providers, so no
model family grades its own family alone. `claude plugin eval` can call only
Anthropic models, so Opus votes during the run and this script adds the other
two afterwards. compare.py then takes the majority of the three.

    uv run --with openai python3 evals/lib/rejudge.py evals/runs/<id> [...] [options]

Options:
    --judge openai|kimi   Judge to run; repeat for both (default: both)
    --dry-run             Count the calls and estimate the cost; call nothing
    --show-prompt         Print the first judge prompt and stop
    --max-cost-usd N      Stop sending calls once this much is spent (default 20)
    --openai-effort E     Reasoning effort for gpt-6-sol (default medium)
    --kimi-effort E       Reasoning effort for kimi-k3 (default high; its own default is max)
    -j N                  Judgments in flight at once (default 8)
    --summary             Print the tables from saved judgments; call nothing

Opus judged each llm check when the run was scored. This asks the same question
of each other judge, with the prompt, system prompt, vote count, and vote rule
`claude plugin eval` 2.1.283 uses, and the grader text from the commit the run
used. It reads the output files keep_run.py copied, so it needs no new agent
runs. A run with no output file fails the check without a call, as the harness
does.

Each judge's votes go to <run>/rejudge/<model>.jsonl, one line per judgment, so
an interrupted re-judge resumes where it stopped. The summary prints how often
each judge agrees with Opus, per check, and each arm's score under each judge,
with the 95% range compare.py uses. Pass an eval batch's three kept runs together to
see the arms side by side.

Keys come from ~/.config/eval-judges/env (OPENAI_API_KEY, MOONSHOT_API_KEY).
Run it on the host only: it refuses inside a container, and it never prints a
key.
"""

import argparse
import json
import re
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from compare import fmt, mean_se, t95  # noqa: E402

KEY_FILE = Path.home() / ".config/eval-judges/env"

# The judge call `claude plugin eval` makes (Claude Code 2.1.283).
SYSTEM = "You are a strict, terse evaluation judge for coding-agent traces."
ASK = "Respond with exactly one word: PASS or FAIL."
VOTES = 3
HEAD, TAIL = 80_000, 20_000  # the harness shows a long file's head and tail

# Price per million tokens, input and output. Cached input is billed as full
# input, so the ceiling errs high. Effort is set, not left to the provider's
# default (Kimi K3's is max), at the middle of each scale: OpenAI takes none,
# low, medium, high, xhigh; Kimi K3 takes low, high, max and always thinks.
JUDGES = {
    "openai": {"model": "gpt-6-sol", "key": "OPENAI_API_KEY", "base_url": None,
               "price": (2.0, 10.0), "effort": "medium"},
    "kimi": {"model": "kimi-k3", "key": "MOONSHOT_API_KEY", "base_url": "https://api.moonshot.ai/v1",
             "price": (3.0, 15.0), "effort": "high"},
}


def prompt(criteria: str, focus: str, text: str) -> str:
    if len(text) > HEAD + TAIL:
        text = f"{text[:HEAD]}\n[…{len(text) - HEAD - TAIL} chars elided…]\n{text[-TAIL:]}"
    return (
        "You are grading the output of a coding agent against a criterion.\n\n"
        f"Criterion:\n{criteria}\n\n\n"
        f"Agent output (file {focus}):\n{text}\n\n\n{ASK}"
    )


def vote(answer: str | None) -> bool:
    """The harness's rule: PASS counts only when the answer never says FAIL."""
    a = answer or ""
    return bool(re.search(r"\bPASS\b", a, re.I)) and not re.search(r"\bFAIL\b", a, re.I)


def split_grader(text: str) -> tuple[dict, str]:
    """A grader file's frontmatter fields (type, focus path) and its criterion."""
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError("grader file has no frontmatter")
    head, body = m.groups()
    meta = {"type": (re.search(r"^type:\s*(\S+)", head, re.M) or [None, None])[1]}
    path = re.search(r"path:\s*([^\s,}]+)", head)
    meta["path"] = path[1] if path else None
    return meta, body.strip()


def grader_at(commit: str, case: str, check: str) -> tuple[dict, str]:
    rel = f"evals/{case}/graders/{check}.md"
    text = subprocess.run(["git", "show", f"{commit}:{rel}"], capture_output=True, text=True, check=True).stdout
    return split_grader(text)


def load_keys() -> dict[str, str]:
    keys = {}
    for line in KEY_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            keys[k.strip()] = v.strip()
    return keys


def in_container() -> bool:
    return Path("/run/.containerenv").exists() or Path("/.dockerenv").exists()


def judgments(run: Path) -> list[dict]:
    """Every llm check in a kept run, with what the judge needs to see."""
    result = json.loads((run / "aggregate-result.json").read_text())
    commit = json.loads((run / "provenance.json").read_text())["commit"]
    graders, out = {}, []
    for case in result["cases"]:
        for arm, runs in case["arms"].items():
            for i, r in enumerate(runs, 1):
                for g in r["graders"]:
                    key = (case["name"], g["name"])
                    if key not in graders:
                        graders[key] = grader_at(commit, *key)
                    meta, criteria = graders[key]
                    if meta["type"] != "llm":
                        continue
                    f = run / "outputs" / case["name"] / f"{arm}-{i}" / meta["path"]
                    out.append({
                        "case": case["name"], "arm": arm, "run": i, "check": g["name"],
                        "focus": meta["path"], "criteria": criteria,
                        "text": f.read_text() if f.exists() else None,
                        "evidence": g.get("evidence"),
                        "opus_votes": g.get("judgeVotes", []), "opus_passed": bool(g["passed"]),
                    })
    return out


def jkey(j: dict) -> tuple:
    return (j["case"], j["arm"], j["run"], j["check"])


def saved(path: Path) -> dict[tuple, dict]:
    if not path.exists():
        return {}
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return {jkey(r): r for r in rows}


class Spend:
    def __init__(self, ceiling: float):
        self.ceiling, self.total, self.lock = ceiling, 0.0, threading.Lock()

    def add(self, usd: float) -> None:
        with self.lock:
            self.total += usd

    def over(self) -> bool:
        with self.lock:
            return self.total >= self.ceiling


def judge_one(client, cfg: dict, j: dict, spend: Spend, secret: str) -> dict:
    row = {k: j[k] for k in ("case", "arm", "run", "check", "opus_votes", "opus_passed")}
    row["model"], row["effort"] = cfg["model"], cfg["effort"]
    if j["text"] is None:
        # The harness fails a missing file without asking the judge.
        return row | {"votes": [], "passed": False, "note": "no output file", "cost_usd": 0.0}
    votes, answers, tin, tout = [], [], 0, 0
    for _ in range(VOTES):
        if spend.over():
            raise RuntimeError("cost ceiling reached")
        try:
            resp = client.chat.completions.create(
                model=cfg["model"],
                reasoning_effort=cfg["effort"],
                messages=[{"role": "system", "content": SYSTEM},
                          {"role": "user", "content": prompt(j["criteria"], j["focus"], j["text"])}],
            )
        except Exception as e:  # the SDK retries transient errors itself
            raise RuntimeError(str(e).replace(secret, "[REDACTED]")) from None
        answer = resp.choices[0].message.content
        u = resp.usage
        tin, tout = tin + u.prompt_tokens, tout + u.completion_tokens
        spend.add((u.prompt_tokens * cfg["price"][0] + u.completion_tokens * cfg["price"][1]) / 1e6)
        votes.append(vote(answer))
        answers.append((answer or "")[:200])
    cost = (tin * cfg["price"][0] + tout * cfg["price"][1]) / 1e6
    return row | {"votes": votes, "passed": sum(votes) > len(votes) / 2, "answers": answers,
                  "input_tokens": tin, "output_tokens": tout, "cost_usd": round(cost, 6)}


def run_judge(name: str, runs: list[Path], all_j: dict[Path, list[dict]], args, keys: dict) -> None:
    from openai import OpenAI

    cfg = JUDGES[name]
    secret = keys.get(cfg["key"], "")
    if not secret:
        sys.exit(f"{cfg['key']} is empty in {KEY_FILE}")
    client = OpenAI(api_key=secret, base_url=cfg["base_url"], max_retries=4, timeout=600)
    spend = Spend(args.max_cost_usd)
    lock = threading.Lock()
    for run in runs:
        out = run / "rejudge" / f"{cfg['model']}.jsonl"
        out.parent.mkdir(exist_ok=True)
        done = saved(out)
        todo = [j for j in all_j[run] if jkey(j) not in done]
        print(f"{name} ({cfg['model']}) on {run}: {len(todo)} to judge, {len(done)} already saved", file=sys.stderr)
        failed = 0
        with ThreadPoolExecutor(args.j) as pool, out.open("a") as fh:
            futures = [pool.submit(judge_one, client, cfg, j, spend, secret) for j in todo]
            for fut in as_completed(futures):
                try:
                    row = fut.result()
                except RuntimeError as e:
                    failed += 1
                    if failed <= 3:
                        print(f"  not judged: {e}", file=sys.stderr)
                    continue
                with lock:
                    fh.write(json.dumps(row) + "\n")
                    fh.flush()
        print(f"  spent so far: ${spend.total:.2f}" + (f"; {failed} not judged, rerun to resume" if failed else ""), file=sys.stderr)
        if spend.over():
            sys.exit(f"cost ceiling ${args.max_cost_usd:.2f} reached; rerun with a higher --max-cost-usd to resume")


def check_evidence(run: Path, js: list[dict]) -> None:
    """The kept file should be the text Opus saw; say so when it is not."""
    off = [j for j in js if j["text"] is not None and j["evidence"] is not None
           and len(j["text"]) <= HEAD + TAIL and j["text"] != j["evidence"]]
    if off:
        print(f"warning: {run}: {len(off)} kept files differ from the text Opus judged, e.g. "
              f"{off[0]['case']}/{off[0]['arm']}-{off[0]['run']}", file=sys.stderr)


def estimate(js: list[dict], cfg: dict) -> float:
    # About 4 characters per token in. Out, a 2026-09-26 smoke test on the
    # triage files measured 15 tokens per vote for gpt-6-sol at medium and 59
    # for kimi-k3 at high, thinking included; 200 leaves room for longer files.
    calls = [j for j in js if j["text"] is not None]
    tin = sum(len(prompt(j["criteria"], j["focus"], j["text"])) + len(SYSTEM) for j in calls) / 4 * VOTES
    tout = len(calls) * VOTES * 200
    return (tin * cfg["price"][0] + tout * cfg["price"][1]) / 1e6


def arm_label(run: Path) -> str:
    for arm in ("none", "this", "official"):
        if run.name.endswith(f"-{arm}"):
            return arm
    return run.name


def scores(run: Path, verdicts: dict[tuple, bool] | None) -> dict[str, list[float]]:
    """Per case, each run's score, with llm checks replaced by another judge's verdicts."""
    result = json.loads((run / "aggregate-result.json").read_text())
    out = {}
    for case in result["cases"]:
        for arm, runs in case["arms"].items():
            for i, r in enumerate(runs, 1):
                num = den = 0.0
                for g in r["graders"]:
                    if not g.get("scored", True):
                        continue
                    passed = bool(g["passed"])
                    if verdicts is not None and (case["name"], arm, i, g["name"]) in verdicts:
                        passed = verdicts[(case["name"], arm, i, g["name"])]
                    w = g.get("weight", 1)
                    num, den = num + w * passed, den + w
                out.setdefault(case["name"], []).append(num / den if den else 0.0)
    return out


def summary(runs: list[Path]) -> None:
    models = sorted({p.stem for run in runs for p in (run / "rejudge").glob("*.jsonl")})
    rows = {m: {} for m in models}
    for run in runs:
        for m in models:
            for k, r in saved(run / "rejudge" / f"{m}.jsonl").items():
                rows[m][(run,) + k] = r
    if not models:
        sys.exit("no saved judgments; run without --summary first")

    print("## Agreement with Opus\n")
    print("A judgment is one check on one run, decided by the majority of its votes.\n")
    print("| Case | Check | " + " | ".join(f"`{m}`" for m in models) + " |")
    print("|---|---|" + "---:|" * len(models))
    checks = sorted({(k[1], k[4]) for m in models for k in rows[m]})
    for case, check in checks + [("**All**", None)]:
        cells = []
        for m in models:
            rs = [r for k, r in rows[m].items() if check is None or (k[1], k[4]) == (case, check)]
            agree = sum(r["passed"] == r["opus_passed"] for r in rs)
            cells.append(f"{agree}/{len(rs)}" if rs else "—")
        print(f"| {case if check is None else '`' + case + '`'} | {'`' + check + '`' if check else ''} | " + " | ".join(cells) + " |")

    print("\n## Scores under each judge\n")
    print("Regex checks keep their result; each llm check takes that judge's verdict. Opus is the score as run.\n")
    judges = ["opus"] + models
    print("| Arm | " + " | ".join(f"`{j}`" for j in judges) + " |")
    print("|---|" + "---:|" * len(judges))
    for run in runs:
        cells = []
        for j in judges:
            if j == "opus":
                per_case = scores(run, None)
            else:
                v = {k[1:]: r["passed"] for k, r in rows[j].items() if k[0] == run}
                per_case = scores(run, v)
            stats = [mean_se(xs) for xs in per_case.values()]
            m = sum(s[0] for s in stats) / len(stats)
            se = (sum(s[1] ** 2 for s in stats) ** 0.5) / len(stats)
            cells.append(fmt(m, 1.96 * se))
        print(f"| {arm_label(run)} | " + " | ".join(cells) + " |")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", type=Path)
    ap.add_argument("--judge", action="append", choices=sorted(JUDGES))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--show-prompt", action="store_true")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--max-cost-usd", type=float, default=20.0)
    ap.add_argument("-j", type=int, default=8)
    for name, cfg in JUDGES.items():
        ap.add_argument(f"--{name}-effort", default=cfg["effort"])
    args = ap.parse_args()
    judges = args.judge or sorted(JUDGES)
    for name, cfg in JUDGES.items():
        cfg["effort"] = getattr(args, f"{name}_effort")

    if args.summary:
        return summary(args.runs)
    all_j = {run: judgments(run) for run in args.runs}
    for run, js in all_j.items():
        check_evidence(run, js)
    if args.show_prompt:
        j = next(j for js in all_j.values() for j in js if j["text"] is not None)
        print(f"[system]\n{SYSTEM}\n\n[user]\n{prompt(j['criteria'], j['focus'], j['text'])}")
        return
    n = sum(len(js) for js in all_j.values())
    for name in judges:
        cfg = JUDGES[name]
        est = sum(estimate(js, cfg) for js in all_j.values())
        print(f"{name} ({cfg['model']}, effort {cfg['effort']}): {n} judgments, up to {n * VOTES} calls, about ${est:.2f}", file=sys.stderr)
    if args.dry_run:
        return
    if in_container():
        sys.exit("refusing to run in a container: the judge keys stay on the host")
    keys = load_keys()
    for name in judges:
        run_judge(name, args.runs, all_j, args, keys)
    summary(args.runs)


if __name__ == "__main__":
    main()
