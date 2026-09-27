#!/usr/bin/env python3
"""Flag log lines that need on-call attention using typesafe.ai's Jev model.

Requires: pip install typesafe-sdk
Requires: TYPESAFE_API_KEY environment variable set.

Usage: python label_logs.py app.log [-o flagged.txt]
"""

import argparse
import asyncio

from typesafe_sdk import AsyncTypeSafeClient, Noul, NoulCriteria, RetryPolicy

MODEL = "jev-latest"
BATCH_SIZE = 40      # log lines bundled into a single API call (batching is far cheaper/faster than one call per line)
CONCURRENCY = 10      # batches in flight at once
THRESHOLD = 0.5       # noul probability above which a line is flagged

QUESTION = (
    "Does this log line describe a problem serious enough that an on-call "
    "engineer should be paged right now (e.g. crash, service outage, unhandled "
    "exception, data loss, security incident, failed health check)? Routine "
    "INFO/DEBUG lines and expected/recovered warnings are not on-call worthy."
)
CRITERIA = NoulCriteria(
    true="Indicates an active failure, outage, or safety/data issue needing human intervention now.",
    false="Routine, informational, or already-handled/recovered - no action needed.",
)


def chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i : i + size]


async def classify_batch(client, sem, batch):
    questions = {
        str(i): Noul(instructions={"log_line": line, "question": QUESTION}, criteria=CRITERIA)
        for i, (_, line) in enumerate(batch)
    }
    async with sem:
        response = await client.system_one(state="", questions=questions, model=MODEL)
    return [(batch[i][0], response.answers[str(i)].noul) for i in range(len(batch))]


async def run(input_path, output_path):
    with open(input_path, encoding="utf-8", errors="replace") as f:
        lines = [line.rstrip("\n") for line in f]

    # Blank lines can't need on-call attention; skip them to save calls.
    indexed = [(i, line) for i, line in enumerate(lines) if line.strip()]
    batches = list(chunked(indexed, BATCH_SIZE))

    sem = asyncio.Semaphore(CONCURRENCY)
    async with AsyncTypeSafeClient(retry=RetryPolicy(max_retries=5)) as client:
        results = await asyncio.gather(*(classify_batch(client, sem, b) for b in batches))

    flagged_indices = {i for batch_result in results for i, score in batch_result if score >= THRESHOLD}

    with open(output_path, "w", encoding="utf-8") as out:
        for i in sorted(flagged_indices):
            out.write(lines[i] + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logfile", help="Path to the log file to scan")
    parser.add_argument("-o", "--output", default="flagged.txt", help="Output path for flagged lines")
    args = parser.parse_args()
    asyncio.run(run(args.logfile, args.output))


if __name__ == "__main__":
    main()
