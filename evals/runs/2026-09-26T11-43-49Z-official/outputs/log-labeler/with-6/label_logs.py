#!/usr/bin/env python3
"""Flag application log lines that need an on-call engineer, using typesafe.ai's Jev model.

Usage:
    TYPESAFE_API_KEY=... python label_logs.py app.log [--output flagged.txt]

Lines are batched into chunks; each chunk becomes one TypeSafe request containing
one Noul question per line (so the document/state is only sent once per chunk),
and chunks are sent concurrently to get through a large log file quickly.
"""

import argparse
import asyncio
import sys
import time

from typesafe_sdk import (
    AsyncTypeSafeClient,
    Noul,
    NoulCriteria,
    RetryPolicy,
    TypeSafeAPIError,
)

NEEDS_ONCALL_INSTRUCTIONS = (
    "Does `lines[{i}]`, a line from an application log, describe something "
    "serious enough that an on-call engineer should be paged right now? "
    "This includes things like crashes, unhandled exceptions, service outages, "
    "failed health checks, data loss or corruption, security incidents, or "
    "resource exhaustion (e.g. out of memory, disk full)."
)
NEEDS_ONCALL_CRITERIA = NoulCriteria(
    true=(
        "The line reports a critical failure, crash, outage, security incident, "
        "or severe resource exhaustion that needs immediate human attention."
    ),
    false=(
        "The line is routine informational, debug, or warning-level output, or "
        "otherwise does not need immediate escalation."
    ),
)


def read_lines(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        raw_lines = [line.rstrip("\n") for line in f]
    return [(i, line) for i, line in enumerate(raw_lines) if line.strip()]


def chunk(items, size):
    for start in range(0, len(items), size):
        yield items[start : start + size]


async def classify_chunk(client, sem, batch, model, retry):
    indices = [i for i, _ in batch]
    texts = [line for _, line in batch]
    questions = {
        f"l{pos}": Noul(
            instructions=NEEDS_ONCALL_INSTRUCTIONS.format(i=pos),
            criteria=NEEDS_ONCALL_CRITERIA,
        )
        for pos in range(len(texts))
    }

    async with sem:
        try:
            response = await client.system_one(
                state={"lines": texts},
                questions=questions,
                model=model,
                retry=retry,
            )
        except TypeSafeAPIError as error:
            print(
                f"warning: chunk with lines {indices[0]}-{indices[-1]} failed "
                f"after retries ({error.status}, request_id={error.request_id}); skipping",
                file=sys.stderr,
            )
            return []

    scores = []
    for pos, original_index in enumerate(indices):
        noul = response.answers[f"l{pos}"].noul
        scores.append((original_index, noul))
    return scores


async def run(args):
    numbered_lines = read_lines(args.log_file)
    if not numbered_lines:
        print("No non-empty lines to classify.", file=sys.stderr)
        open(args.output, "w").close()
        return

    text_by_index = dict(numbered_lines)
    batches = list(chunk(numbered_lines, args.chunk_size))
    sem = asyncio.Semaphore(args.concurrency)
    retry = RetryPolicy(max_retries=5, backoff_max=8.0, timeout=30.0)

    start = time.monotonic()
    done = 0
    scored = {}

    async with AsyncTypeSafeClient() as client:
        tasks = [
            asyncio.create_task(classify_chunk(client, sem, batch, args.model, retry))
            for batch in batches
        ]
        for task in asyncio.as_completed(tasks):
            for original_index, noul in await task:
                scored[original_index] = noul
            done += 1
            if done % 10 == 0 or done == len(tasks):
                elapsed = time.monotonic() - start
                print(
                    f"processed {done}/{len(tasks)} chunks "
                    f"({len(numbered_lines)} lines) in {elapsed:.1f}s",
                    file=sys.stderr,
                )

    flagged_indices = sorted(
        i for i, noul in scored.items() if noul >= args.threshold
    )
    with open(args.output, "w", encoding="utf-8") as f:
        for i in flagged_indices:
            f.write(text_by_index[i] + "\n")

    print(
        f"flagged {len(flagged_indices)}/{len(numbered_lines)} lines -> {args.output}",
        file=sys.stderr,
    )


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_file", help="Path to the log file to scan")
    parser.add_argument(
        "--output", default="flagged.txt", help="Where to write flagged lines"
    )
    parser.add_argument(
        "--model", default="jev-latest", help="TypeSafe model to use"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=100,
        help="Log lines per TypeSafe request (one Noul question per line)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=20,
        help="Number of chunk requests to run concurrently",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.7,
        help="Minimum Noul probability to flag a line",
    )
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
