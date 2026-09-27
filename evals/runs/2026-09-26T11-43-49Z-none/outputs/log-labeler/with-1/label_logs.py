#!/usr/bin/env python3
"""Flag log lines that need on-call attention using TypeSafe AI's Jev model.

Lines are grouped into batches and each batch is sent to the model as a
single request containing one Noul (yes/no) question per line, referencing
that line's own field in `state` (per TypeSafe's batching guidance: asking
many questions in one call is much cheaper/faster than one call per
question). Batches are then run concurrently to get through a large file
quickly.
"""

import argparse
import asyncio
import os
import sys

from typesafe_sdk import AsyncTypeSafeClient, Noul, RetryPolicy

MODEL = "jev-latest"
BATCH_SIZE = 50
CONCURRENCY = 20
YES_THRESHOLD = 0.5

QUESTION_TEMPLATE = (
    "Does the log line `{key}` indicate a problem serious enough that an "
    "on-call engineer should be paged right now (e.g. crashes, unhandled "
    "exceptions, failed health checks, resource exhaustion, security "
    "incidents, data loss)? Routine INFO/DEBUG messages and expected "
    "warnings do not need on-call attention."
)


def read_lines(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return [line.rstrip("\n") for line in f if line.strip()]


def batched(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


async def classify_batch(client, semaphore, lines):
    keys = [f"line_{i}" for i in range(len(lines))]
    state = dict(zip(keys, lines))
    questions = {key: Noul(instructions=QUESTION_TEMPLATE.format(key=key)) for key in keys}

    async with semaphore:
        response = await client.system_one(state=state, questions=questions, model=MODEL)

    return [line for key, line in zip(keys, lines) if response.answers[key].noul >= YES_THRESHOLD]


async def run(input_path, output_path):
    lines = read_lines(input_path)
    if not lines:
        open(output_path, "w").close()
        print("No non-blank lines found; wrote empty flagged file.")
        return

    semaphore = asyncio.Semaphore(CONCURRENCY)
    async with AsyncTypeSafeClient(retry=RetryPolicy(max_retries=5)) as client:
        tasks = [classify_batch(client, semaphore, batch) for batch in batched(lines, BATCH_SIZE)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    flagged = []
    failed_batches = 0
    for result in results:
        if isinstance(result, Exception):
            failed_batches += 1
            continue
        flagged.extend(result)

    with open(output_path, "w", encoding="utf-8") as f:
        for line in flagged:
            f.write(line + "\n")

    print(f"Scanned {len(lines)} lines, flagged {len(flagged)} for on-call review -> {output_path}")
    if failed_batches:
        print(f"Warning: {failed_batches} batch(es) failed after retries and were skipped.", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logfile", help="Path to the log file to scan")
    parser.add_argument("-o", "--output", default="flagged.txt", help="Output file for flagged lines")
    args = parser.parse_args()

    if not os.environ.get("TYPESAFE_API_KEY"):
        sys.exit("TYPESAFE_API_KEY environment variable is not set")

    asyncio.run(run(args.logfile, args.output))


if __name__ == "__main__":
    main()
