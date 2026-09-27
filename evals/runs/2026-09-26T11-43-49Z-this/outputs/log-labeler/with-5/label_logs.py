#!/usr/bin/env python3
"""Flag application log lines that likely need an on-call engineer, using TypeSafe's Jev model.

Requires: pip install typesafe-sdk   (or: uv add typesafe-sdk)
          export TYPESAFE_API_KEY=...

Usage:
    python label_logs.py app.log
    python label_logs.py app.log --out flagged.txt --batch-size 50 --workers 8 --threshold 0.7
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from typesafe_sdk import Noul, NoulCriteria, TypeSafeClient, TypeSafeError

# Pin the model version: the threshold below is tuned against it, and answers
# can shift when a "latest" alias moves to a new release.
MODEL = "jev-1.13.0"

# Lines per API request. One line = one Noul question, all in a single call.
# Batching many items into one request is far cheaper and faster than one
# request per line (state dominates tokens, so extra questions are nearly
# free). A typical log line leaves huge headroom under the 64k-token
# state+questions limit at this batch size; shrink it if your lines are
# unusually long (e.g. embedded stack traces).
BATCH_SIZE = 50

# Concurrent requests. This is the practical ceiling on a shared API key
# before the endpoint starts rate-limiting (429s).
MAX_WORKERS = 8

# Flag a line when P(needs on-call) is at or above this. Noul values below
# ~0.30 are confidently "no", above ~0.70 are confidently "yes", and the
# middle band is where the model is guessing. Start here and retune on your
# own labeled examples.
NOUL_THRESHOLD = 0.70

NEEDS_ONCALL_CRITERIA = NoulCriteria(
    true=(
        "The line reports a crash, unhandled exception, service outage, failed "
        "health/readiness check, data loss or corruption risk, security breach, "
        "cascading failure, or resource exhaustion (out of memory, disk full, "
        "connection pool exhausted, thread starvation) that is actively "
        "degrading or about to degrade production right now."
    ),
    false=(
        "The line is routine informational, debug, or trace output; a warning "
        "about a transient or already-recovered condition; a validation error "
        "caused by bad client input; or anything else that does not call for "
        "immediate human intervention."
    ),
)


def make_question(i: int) -> Noul:
    return Noul(
        instructions=(
            f"Does the log line at `lines[{i}]` describe a problem serious "
            "enough that an on-call engineer should be paged right now, as "
            "opposed to routine or already-handled output?"
        ),
        criteria=NEEDS_ONCALL_CRITERIA,
    )


def label_batch(
    client: TypeSafeClient, batch: list[str], threshold: float
) -> list[bool]:
    """Return, per line in batch, whether it needs an on-call engineer."""
    questions = {f"q{i}": make_question(i) for i in range(len(batch))}
    try:
        response = client.system_one(state={"lines": batch}, questions=questions)
    except TypeSafeError as e:
        print(f"warning: a batch of {len(batch)} lines failed ({e}); skipping", file=sys.stderr)
        return [False] * len(batch)
    return [response.nouls[f"q{i}"].noul >= threshold for i in range(len(batch))]


def chunked(seq: list, size: int):
    for start in range(0, len(seq), size):
        yield seq[start : start + size]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("logfile", type=Path, help="path to the log file, one entry per line")
    parser.add_argument("-o", "--out", type=Path, default=Path("flagged.txt"), help="output file for flagged lines")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="log lines per API request")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS, help="concurrent requests")
    parser.add_argument("--threshold", type=float, default=NOUL_THRESHOLD, help="P(needs on-call) cutoff to flag a line")
    parser.add_argument("--model", default=MODEL, help="Jev model version to pin")
    args = parser.parse_args()

    with args.logfile.open(encoding="utf-8", errors="replace") as f:
        lines = [line.rstrip("\n") for line in f]
    # Blank lines can never need paging; drop them before spending a request on them.
    lines = [line for line in lines if line.strip()]

    batches = list(chunked(lines, args.batch_size))
    total_batches = len(batches)

    with TypeSafeClient(model=args.model) as client, ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(label_batch, client, batch, args.threshold) for batch in batches]

        flagged_count = 0
        with args.out.open("w", encoding="utf-8") as out:
            for batch_index, (batch, future) in enumerate(zip(batches, futures), start=1):
                flags = future.result()
                for line, flagged in zip(batch, flags):
                    if flagged:
                        out.write(line + "\n")
                        flagged_count += 1
                if batch_index % 100 == 0 or batch_index == total_batches:
                    print(f"processed {batch_index}/{total_batches} batches", file=sys.stderr)

    print(f"Flagged {flagged_count} of {len(lines)} lines -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
