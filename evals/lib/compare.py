"""Compare the arms of one eval batch, with a 95% range on every number.

    python3 evals/lib/compare.py [--as-run] <batch stamp>
    python3 evals/lib/compare.py [--as-run] none=<dir> this=<dir> official=<dir>

A batch stamp names evals/runs/<stamp>-{none,this,official} once the eval batch
is kept, and evals/results/<stamp>-{none,this,official} before that. Any arm can
instead be given as a directory holding an aggregate-result.json.

llm checks are scored by a panel: the judge that scored the run, plus each judge
in the run's rejudge/ directory (see rejudge.py). Each judge's own three-vote
verdict is one vote, and a check passes when most judges pass it. A run with no
rejudge/ keeps the verdicts it ran with, and --as-run forces that.

Prints Markdown: each arm's score per case and overall, then how far this plugin
sits above each other arm (this plugin minus that arm, so positive means this
plugin scored higher), then the passing runs per check, with this plugin's count minus each other
arm's. 🟢 marks a lead and 🔴 a deficit that a 95% Newcombe interval on the two
pass rates says chance does not explain. A score is a run's share
of scored checks, averaged over the arm's runs. The range is a t interval on
those per-run scores; Δ uses the two arms' standard errors combined. An arm
whose runs all score the same shows ±0.00, which says only that those runs
agreed, not that the score is exact. Compare arms from one eval batch only.
"""

import json
import math
import sys
from pathlib import Path

ARMS = ("this", "none", "official")
REF = "this"
LABELS = {"none": "No plugin", "this": "This plugin", "official": "Official"}
# Two-sided 95% t critical values by degrees of freedom; 1.96 beyond the table.
T95 = {1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57, 6: 2.45, 7: 2.36, 8: 2.31,
       9: 2.26, 10: 2.23, 12: 2.18, 15: 2.13, 20: 2.09, 30: 2.04}


def t95(df: int) -> float:
    if df < 1:
        return float("nan")
    return next((T95[k] for k in sorted(T95) if k >= df), 1.96)


def panel(path: Path, result: dict) -> tuple[list[str], dict[tuple, bool]]:
    """The judges on the panel, and the majority verdict for each llm check they judged."""
    files = sorted((path / "rejudge").glob("*.jsonl"))
    if not files:
        return [], {}
    judges = [result.get("suite", {}).get("judgeModel") or "as run"] + [f.stem for f in files]
    if len(judges) % 2 == 0:
        sys.exit(f"{path}: {len(judges)} judges can tie; a panel needs an odd number")
    votes = {}
    for f in files:
        for line in f.read_text().splitlines():
            j = json.loads(line)
            key = (j["case"], j["arm"], j["run"], j["check"])
            votes.setdefault(key, [j["opus_passed"]]).append(bool(j["passed"]))
    short = [k for k, v in votes.items() if len(v) != len(judges)]
    if short:
        sys.exit(f"{path}: {len(short)} llm checks lack a verdict from every judge; finish rejudge.py first")
    return judges, {k: sum(v) * 2 > len(v) for k, v in votes.items()}


def graded_runs(result: dict, verdicts: dict[tuple, bool]) -> dict[str, list[dict[str, bool]]]:
    """Per case, each run's scored checks and whether each passed."""
    out = {}
    for case in result["cases"]:
        arms = case["arms"]
        if len(arms) != 1:
            sys.exit(f"{case['name']} has arms {sorted(arms)}; compare.py expects one arm per result")
        arm, runs = next(iter(arms.items()))
        out[case["name"]] = [
            {g["name"]: (verdicts.get((case["name"], arm, i, g["name"]), bool(g["passed"])), g.get("weight", 1))
             for g in r["graders"] if g.get("scored", True)}
            for i, r in enumerate(runs, 1)
        ]
    return out


def run_scores(graded: dict[str, list[dict]]) -> dict[str, list[float]]:
    """Per case, each run's weighted share of passed checks."""
    scores = {}
    for case, runs in graded.items():
        scores[case] = []
        for checks in runs:
            den = sum(w for _, w in checks.values())
            scores[case].append(sum(w for p, w in checks.values() if p) / den if den else 0.0)
    return scores


def check_passes(graded: dict[str, list[dict]]) -> dict[tuple[str, str], tuple[int, int]]:
    out = {}
    for case, runs in graded.items():
        for checks in runs:
            for name, (passed, _) in checks.items():
                p, n = out.get((case, name), (0, 0))
                out[(case, name)] = (p + passed, n + 1)
    return out


def wilson(p: int, n: int) -> tuple[float, float]:
    z = 1.96
    q = p / n
    d = 1 + z * z / n
    c = (q + z * z / (2 * n)) / d
    h = z * math.sqrt(q * (1 - q) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def newcombe_lead(p1: int, n1: int, p0: int, n0: int) -> bool:
    """Whether a 95% Newcombe interval on the difference of two pass rates lies above zero."""
    (l1, _), (_, u0) = wilson(p1, n1), wilson(p0, n0)
    q1, q0 = p1 / n1, p0 / n0
    return q1 - q0 - math.sqrt((q1 - l1) ** 2 + (u0 - q0) ** 2) > 0


def mean_se(xs: list[float]) -> tuple[float, float, int]:
    n = len(xs)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1)) if n > 1 else float("nan")
    return m, sd / math.sqrt(n), n


def fmt(m: float, half: float, signed: bool = False) -> str:
    s = f"{m:+.2f}" if signed and abs(m) >= 0.005 else f"{m:.2f}"
    return s if math.isnan(half) else f"{s} ± {half:.2f}"


def lead_cell(p1: int, n1: int, p0: int, n0: int) -> str:
    """This plugin's pass count minus the other arm's, marked when chance can't explain it."""
    d = p1 - p0
    text = "0" if d == 0 else f"+{d}" if d > 0 else f"−{-d}"
    if newcombe_lead(p1, n1, p0, n0):
        return f"🟢 **{text}**"
    if newcombe_lead(p0, n0, p1, n1):
        return f"🔴 **{text}**"
    return text


def load(args: list[str]) -> dict[str, tuple[Path, dict]]:
    if len(args) == 1 and "=" not in args[0]:
        kept = Path("evals/runs") / f"{args[0]}-{REF}"
        base = Path("evals/runs") if kept.exists() else Path("evals/results")
        paths = {arm: base / f"{args[0]}-{arm}" for arm in ARMS}
    else:
        paths = dict(a.split("=", 1) for a in args)
        paths = {arm: Path(p) for arm, p in paths.items() if arm in ARMS}
    results = {}
    for arm, path in paths.items():
        f = path / "aggregate-result.json"
        if f.exists():
            results[arm] = (path, json.loads(f.read_text()))
        else:
            print(f"<!-- no {arm} arm: {f} not found -->")
    if REF not in results:
        sys.exit("need this plugin's arm: every other arm is measured against it")
    return results


def main(args: list[str]) -> None:
    as_run = "--as-run" in args
    results = load([a for a in args if a != "--as-run"])
    arms = [a for a in ARMS if a in results]
    graded, panels = {}, set()
    for a in arms:
        path, result = results[a]
        judges, verdicts = ([], {}) if as_run else panel(path, result)
        panels.add(", ".join(judges) or "as run")
        graded[a] = graded_runs(result, verdicts)
    if len(panels) > 1:
        sys.exit(f"the arms were judged differently ({'; '.join(sorted(panels))}); re-judge every arm, or pass --as-run")
    scores = {a: run_scores(graded[a]) for a in arms}
    cases = list(scores[REF])
    runs = {a: sorted({len(v) for v in scores[a].values()}) for a in arms}
    print("Runs per case: " + ", ".join(f"{LABELS[a]} {'/'.join(map(str, runs[a]))}" for a in arms))
    print(f"llm checks judged by: {panels.pop()}\n")

    others = [a for a in arms if a != REF]
    header = ["Case"] + [LABELS[a] for a in arms] + [f"This plugin vs {LABELS[a].lower()}" for a in others]
    print("| " + " | ".join(header) + " |")
    print("|---|" + "---:|" * (len(header) - 1))
    totals = {a: [] for a in arms}
    for case in cases:
        stats = {a: mean_se(scores[a][case]) for a in arms if case in scores[a]}
        for a, st in stats.items():
            totals[a].append(st)
        cells = [fmt(m, t95(n - 1) * se) for m, se, n in stats.values()]
        for a in others:
            if a in stats:
                (m1, se1, n1), (m0, se0, n0) = stats[REF], stats[a]
                cells.append(fmt(m1 - m0, t95(min(n1, n0) - 1) * math.hypot(se1, se0), signed=True))
            else:
                cells.append("—")
        print(f"| `{case}` | " + " | ".join(cells) + " |")

    # The overall score is the mean of the case scores, as the harness reports it.
    overall = {}
    for a in arms:
        k = len(totals[a])
        overall[a] = (sum(m for m, _, _ in totals[a]) / k, math.sqrt(sum(se ** 2 for _, se, _ in totals[a])) / k)
    cells = [fmt(m, 1.96 * se) for m, se in overall.values()]
    for a in others:
        (m1, se1), (m0, se0) = overall[REF], overall[a]
        cells.append(fmt(m1 - m0, 1.96 * math.hypot(se1, se0), signed=True))
    print("| **Mean** | " + " | ".join(f"**{c}**" for c in cells) + " |")

    print("\n| Case | Check | " + " | ".join(LABELS[a] for a in arms)
          + " | " + " | ".join(f"This plugin vs {LABELS[a].lower()}" for a in others) + " |")
    print("|---|---|" + "---:|" * (len(arms) + len(others)))
    passes = {a: check_passes(graded[a]) for a in arms}
    last = None
    for case, check in passes[REF]:
        cells = []
        for a in arms:
            p, n = passes[a].get((case, check), (0, 0))
            cells.append(f"{p}/{n}" if n else "—")
        p1, n1 = passes[REF][(case, check)]
        for a in others:
            p0, n0 = passes[a].get((case, check), (0, 0))
            if not n0:
                cells.append("—")
                continue
            cells.append(lead_cell(p1, n1, p0, n0))
        print(f"| {'`' + case + '`' if case != last else ''} | `{check}` | " + " | ".join(cells) + " |")
        last = case


if __name__ == "__main__":
    if not sys.argv[1:]:
        sys.exit(__doc__)
    main(sys.argv[1:])
