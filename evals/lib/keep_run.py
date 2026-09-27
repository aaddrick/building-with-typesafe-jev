"""Keep a finished run: copy its record into evals/runs/<id>/ for git.

    python3 evals/lib/keep_run.py evals/results/<dir> <id>

Copies aggregate-result.json, provenance.json, usage.json, and
official-commit.txt when present, plus the file each agent wrote, as outputs/<case>/<arm>-<n>/<file>.
Those files are what the judges read, a few KB each, so any kept run can be
re-judged from git without new agent runs. Full traces stay in
evals/results/tmp/, which git ignores.

The output file is the one a case's graders name (gate.py, triage.py, ...),
found by name in the run's kept directory. A run that wrote no file gets a
MISSING marker, so its absence is on record too. Secrets that record_finish
would scrub are refused here: the script stops before copying anything.
"""

import json
import os
import re
import shutil
import sys
from pathlib import Path

SECRET = re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}")


def output_name(case: dict) -> str | None:
    for grader in case["graders"]:
        focus = grader.get("config", {}).get("focus") or {}
        if isinstance(focus, dict) and focus.get("source") == "file":
            return focus["path"]
    return None


class unsealed:
    """Open a kept run's sealed directories read-only, and seal them again after.

    The harness keeps the agent's workspace under sealed/ at mode 000, since the
    plugin under test wrote it. This only reads files there, never runs anything
    in it, as the harness asks, and restores every mode it changed.
    """

    def __init__(self, kept: Path):
        self.kept, self.changed = kept, []

    def __enter__(self):
        for root, dirs, _ in os.walk(self.kept):
            for d in list(dirs):
                path = Path(root) / d
                mode = path.stat().st_mode
                if not os.access(path, os.R_OK | os.X_OK):
                    os.chmod(path, mode | 0o500)
                    self.changed.append((path, mode))
        return self

    def __exit__(self, *exc):
        for path, mode in reversed(self.changed):
            os.chmod(path, mode)


def find_output(kept: Path, name: str) -> Path | None:
    hits = [Path(root) / name for root, _, files in os.walk(kept) if name in files]
    return min(hits, key=lambda h: len(h.parts)) if hits else None


def main(results: str, run_id: str) -> None:
    src, dst = Path(results), Path("evals/runs") / run_id
    result = json.loads((src / "aggregate-result.json").read_text())
    if dst.exists():
        sys.exit(f"{dst} exists; pick another id")

    plan, kept_dirs = [], []
    for case in result["cases"]:
        name = output_name(case)
        for arm, runs in case["arms"].items():
            for i, run in enumerate(runs, 1):
                trace = run.get("tracePath") or ""
                trace = trace.replace("/out/", "./", 1) if trace.startswith("/out/") else trace
                kept = Path(trace).parent.parent if trace else None
                plan.append((Path("outputs") / case["name"] / f"{arm}-{i}", name, kept))

    # Read every output while its run's sealed directories are open, then close them.
    contents = []
    for rel, name, kept in plan:
        text = None
        if kept and name and kept.exists():
            with unsealed(kept):
                found = find_output(kept, name)
                text = found.read_text(errors="replace") if found else None
        if text and SECRET.search(text):
            sys.exit(f"{rel}/{name} holds something shaped like a key; scrub it before keeping")
        contents.append((rel, name, text))

    dst.mkdir(parents=True)
    for extra in ("aggregate-result.json", "provenance.json", "usage.json", "official-commit.txt"):
        if (src / extra).exists():
            shutil.copy(src / extra, dst / extra)
    missing = 0
    for rel, name, text in contents:
        (dst / rel).mkdir(parents=True)
        if text is not None:
            (dst / rel / name).write_text(text)
        else:
            missing += 1
            (dst / rel / "MISSING").write_text(f"No {name} in this run's kept directory.\n")
    print(f"Kept {dst}: {len(contents) - missing} output files, {missing} missing")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
