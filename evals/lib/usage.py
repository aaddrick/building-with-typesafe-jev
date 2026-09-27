"""Record each run's token usage, so it can be kept without the traces.

    python3 evals/lib/usage.py <results dir>           # write <dir>/usage.json
    python3 evals/lib/usage.py --table <dir> [...]     # print a Markdown table

A trace ends with a result event that sums the agent's tokens and cost. Traces
stay in evals/results/tmp/, which git ignores because they hold whatever an
agent read, so this copies only the counts into usage.json, one entry per run,
next to aggregate-result.json. record_finish writes it; keep_run.py keeps it.

--table sums usage.json per directory, and adds each judge in the directory's
rejudge/ from its own saved counts. The in-run judge records a cost but no
tokens, so its row has none.
"""

import json
import sys
from pathlib import Path

FIELDS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")


def trace_path(run: dict) -> Path | None:
    path = run.get("tracePath") or ""
    # The container writes /out/...; that is the repo root on the host.
    return Path(path.replace("/out/", "./", 1) if path.startswith("/out/") else path) if path else None


def result_event(path: Path) -> dict | None:
    last = None
    try:
        for line in path.open():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if isinstance(event, dict) and event.get("type") == "result":
                last = event
    except OSError:
        return None
    return last


def usage(results: Path) -> list[dict]:
    result = json.loads((results / "aggregate-result.json").read_text())
    out = []
    for case in result["cases"]:
        for arm, runs in case["arms"].items():
            for i, run in enumerate(runs, 1):
                row = {"case": case["name"], "arm": arm, "run": i}
                path = trace_path(run)
                event = result_event(path) if path else None
                if event is None:
                    out.append(row | {"missing": True})
                    continue
                u = event.get("usage") or {}
                row |= {k: u.get(k, 0) for k in FIELDS}
                row["thinking_tokens"] = (u.get("output_tokens_details") or {}).get("thinking_tokens", 0)
                row["models"] = sorted(event.get("modelUsage") or {})
                row["cost_usd"] = event.get("total_cost_usd")
                out.append(row)
    return out


def write(results: Path) -> None:
    rows = usage(results)
    (results / "usage.json").write_text(json.dumps(rows, indent=1) + "\n")
    missing = sum(1 for r in rows if r.get("missing"))
    if missing:
        print(f"usage.json: {missing} of {len(rows)} runs had no readable trace", file=sys.stderr)


def m(n: int) -> str:
    return f"{n / 1e6:.2f}M" if n >= 1e6 else f"{n / 1e3:.0f}K" if n >= 1e4 else f"{n:,}"


def table(dirs: list[Path]) -> None:
    print("| Who | Runs or calls | Cache writes | Cache reads | Uncached input | Output (thinking) |")
    print("|---|---:|---:|---:|---:|---:|")
    judges = {}
    for d in dirs:
        rows = [r for r in json.loads((d / "usage.json").read_text()) if not r.get("missing")]
        s = {k: sum(r[k] for r in rows) for k in FIELDS + ("thinking_tokens",)}
        print(f"| Agent, `{d.name}` | {len(rows)} | {m(s['cache_creation_input_tokens'])} | "
              f"{m(s['cache_read_input_tokens'])} | {m(s['input_tokens'])} | "
              f"{m(s['output_tokens'])} ({m(s['thinking_tokens'])}) |")
        for f in sorted((d / "rejudge").glob("*.jsonl")):
            j = judges.setdefault(f.stem, [0, 0, 0])
            for line in f.read_text().splitlines():
                r = json.loads(line)
                j[0] += len(r.get("votes", []))
                j[1] += r.get("input_tokens", 0)
                j[2] += r.get("output_tokens", 0)
    for name, (calls, tin, tout) in judges.items():
        print(f"| Judge, `{name}` | {calls:,} | — | — | {m(tin)} | {m(tout)} |")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--table"] and args[1:]:
        table([Path(a) for a in args[1:]])
    elif len(args) == 1:
        write(Path(args[0]))
    else:
        sys.exit(__doc__)
