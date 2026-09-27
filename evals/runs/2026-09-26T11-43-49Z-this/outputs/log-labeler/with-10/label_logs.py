#!/usr/bin/env python3
"""
Flag log lines that need an on-call engineer, using TypeSafe's Jev model.

Usage:
    export TYPESAFE_API_KEY=...
    python3 label_logs.py app.log [-o flagged.txt]

Requires: pip install typesafe-sdk
"""
from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from typesafe_sdk import (
    Noul,
    NoulCriteria,
    RetryPolicy,
    TypeSafeClient,
    TypeSafeError,
)

# --- tunables -----------------------------------------------------------
# Lines per request. Batching amortizes the per-request overhead: the docs
# report batched calls run about 10x faster and 12x cheaper than one
# question per call. Well within the 64k token state+questions budget for
# ordinary log lines.
BATCH_SIZE = 50

# Concurrent in-flight requests. The API rate-limits a shared key above
# about 8 concurrent workers.
MAX_WORKERS = 8

# Noul >= this is flagged. Kept low (rather than the "confident yes" bar of
# 0.7) because flagged.txt IS the human review step here: anything that
# isn't confidently "no" should surface to the on-call engineer rather than
# be silently dropped. Tune upward if this is too noisy for your logs.
FLAG_THRESHOLD = 0.3

MODEL = None  # None = jev-latest. Pin e.g. "jev-1.13.0" once you've tuned
# FLAG_THRESHOLD against a specific model version's answers.

QUESTION_INSTRUCTIONS = (
    "Does the log line `lines[{i}]` describe a problem that needs a human "
    "on-call engineer to look at right now: for example a crash, an "
    "unhandled exception, a service outage, data loss or corruption, a "
    "security incident, or a resource (disk/memory/CPU/connections) "
    "exhausted to the point of failure? Routine INFO/DEBUG output, "
    "expected warnings, and errors that were retried or recovered on "
    "their own do not need paging."
)
NOUL_CRITERIA = NoulCriteria(
    true=(
        "Describes an active failure, crash, outage, data loss, security "
        "incident, or exhausted resource that a person should act on now."
    ),
    false=(
        "Routine informational or debug output, an expected or already-"
        "handled warning, or an error that recovered on its own."
    ),
)
# --------------------------------------------------------------------------


def build_questions(batch_size: int) -> dict:
    return {
        f"line_{i}": Noul(
            instructions=QUESTION_INSTRUCTIONS.format(i=i),
            criteria=NOUL_CRITERIA,
        )
        for i in range(batch_size)
    }


def classify_batch(client: TypeSafeClient, batch: list[str]) -> list[bool]:
    """Return one flag per line in `batch`. Fails safe: on an unrecoverable
    API error, flags every line in the batch rather than silently dropping
    lines an on-call engineer might have needed to see."""
    try:
        response = client.system_one(
            state={"lines": batch},
            questions=build_questions(len(batch)),
            model=MODEL,
        )
    except TypeSafeError as exc:
        print(f"warning: batch failed ({exc}); flagging batch for manual review", file=sys.stderr)
        return [True] * len(batch)

    return [
        response.nouls[f"line_{i}"].noul >= FLAG_THRESHOLD for i in range(len(batch))
    ]


def chunk(items: list[str], size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logfile", help="path to the log file, one entry per line")
    parser.add_argument("-o", "--output", default="flagged.txt", help="output path (default: flagged.txt)")
    args = parser.parse_args()

    with open(args.logfile, encoding="utf-8", errors="replace") as f:
        lines = [line.rstrip("\n") for line in f if line.strip()]

    if not lines:
        print("no non-empty lines to process")
        open(args.output, "w").close()
        return

    batches = list(chunk(lines, BATCH_SIZE))
    print(f"{len(lines)} lines in {len(batches)} batches of up to {BATCH_SIZE}, {MAX_WORKERS} workers")

    start = time.monotonic()
    flagged_count = 0

    with TypeSafeClient(retry=RetryPolicy(max_retries=5)) as client, open(args.output, "w", encoding="utf-8") as out:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            done = 0
            # pool.map preserves input order in its output even though the
            # requests themselves run concurrently, so batches can be
            # written straight through without re-sorting.
            for batch, flags in zip(batches, pool.map(lambda b: classify_batch(client, b), batches)):
                for line, flagged in zip(batch, flags):
                    if flagged:
                        out.write(line + "\n")
                        flagged_count += 1
                done += 1
                if done % 50 == 0 or done == len(batches):
                    print(f"  {done}/{len(batches)} batches", file=sys.stderr)

    elapsed = time.monotonic() - start
    print(f"flagged {flagged_count}/{len(lines)} lines in {elapsed:.1f}s -> {args.output}")


if __name__ == "__main__":
    main()
