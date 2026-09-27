#!/usr/bin/env python3
"""Flag log lines that need on-call attention using typesafe.ai's Jev model.

Lines are grouped into chunks and sent as a single `state` array per request,
with one Noul question per line in the chunk ("speculative fan-out"). This
keeps the per-line cost low, since the document (the chunk) is paid for once
per request instead of once per line. Chunks are processed concurrently with
a bounded semaphore so the whole file finishes quickly.

Requires TYPESAFE_API_KEY to be set in the environment.
"""

import argparse
import asyncio
import sys

from typesafe_sdk import AsyncTypeSafeClient, Noul, RetryPolicy

ON_CALL_INSTRUCTIONS = (
    "state[{i}] is one line from an application log. Does it describe something "
    "serious enough that an on-call engineer should be paged or notified right now "
    "-- e.g. a crash, unhandled exception, service outage, data loss, security "
    "incident, or a dependency becoming unavailable? Routine INFO/DEBUG lines, "
    "expected warnings, and successful operations are 'no'."
)


def chunk_lines(lines, size):
    for i in range(0, len(lines), size):
        yield lines[i : i + size]


async def classify_chunk(client, semaphore, chunk, model, threshold):
    questions = {
        f"line_{i}": Noul(instructions=ON_CALL_INSTRUCTIONS.format(i=i))
        for i in range(len(chunk))
    }
    async with semaphore:
        response = await client.system_one(state=chunk, questions=questions, model=model)

    flagged = []
    for i, line in enumerate(chunk):
        answer = response.answers.get(f"line_{i}")
        if answer is not None and answer.noul >= threshold:
            flagged.append(line)
    return flagged


async def run(args):
    with open(args.input, "r", errors="replace") as f:
        lines = [line.rstrip("\n") for line in f]

    chunks = list(chunk_lines(lines, args.chunk_size))
    results = [None] * len(chunks)
    semaphore = asyncio.Semaphore(args.concurrency)
    retry = RetryPolicy(http_statuses={408, 429, 500, 502, 503, 504, 529})
    done = 0

    async def worker(idx, chunk):
        nonlocal done
        try:
            results[idx] = await classify_chunk(
                client, semaphore, chunk, args.model, args.threshold
            )
        except Exception as exc:
            print(f"chunk {idx} failed, skipping: {exc}", file=sys.stderr)
            results[idx] = []
        done += 1
        if done % 20 == 0 or done == len(chunks):
            print(f"{done}/{len(chunks)} chunks processed", file=sys.stderr)

    async with AsyncTypeSafeClient(retry=retry) as client:
        await asyncio.gather(*(worker(i, c) for i, c in enumerate(chunks)))

    with open(args.output, "w") as f:
        for chunk_result in results:
            for line in chunk_result:
                f.write(line + "\n")

    total_flagged = sum(len(r) for r in results)
    print(f"Flagged {total_flagged}/{len(lines)} lines -> {args.output}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Flag log lines needing on-call attention using typesafe.ai's Jev model."
    )
    parser.add_argument("input", help="Path to the log file (one entry per line)")
    parser.add_argument("-o", "--output", default="flagged.txt", help="Output file for flagged lines")
    parser.add_argument("--chunk-size", type=int, default=40, help="Log lines per API call")
    parser.add_argument("--concurrency", type=int, default=20, help="Max concurrent API calls")
    parser.add_argument("--model", default="jev-latest", help="Jev model to use")
    parser.add_argument(
        "--threshold", type=float, default=0.5, help="Noul probability at/above which a line is flagged"
    )
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
