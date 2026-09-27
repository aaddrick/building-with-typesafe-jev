#!/usr/bin/env python3
"""Flag log lines that need on-call engineer attention using typesafe.ai's Jev model."""

import argparse
import asyncio
import sys

from typesafe_sdk import AsyncTypeSafeClient, Noul, RetryPolicy, TypeSafeAPIError

BATCH_SIZE = 25       # log lines packed into a single request (one Noul question per line)
CONCURRENCY = 20      # requests in flight at once
THRESHOLD = 0.5       # noul probability above which a line is flagged

CRITERIA = {
    "true": "The line signals an active incident requiring immediate human intervention.",
    "false": "The line is routine, informational, or a transient/expected warning.",
}


def read_batches(path, batch_size):
    batch = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line_no, raw_line in enumerate(f):
            line = raw_line.rstrip("\n")
            if not line.strip():
                continue
            batch.append((line_no, line))
            if len(batch) >= batch_size:
                yield batch
                batch = []
    if batch:
        yield batch


async def process_batch(client, semaphore, batch, threshold):
    keys = [f"l{line_no}" for line_no, _ in batch]
    state = {"lines": {key: text for key, (_, text) in zip(keys, batch)}}
    questions = {
        key: Noul(
            instructions=(
                f"Does the log line at `lines.{key}` describe a problem serious "
                "enough that an on-call engineer should be paged right now "
                "(e.g. an outage, crash, data loss, security incident, or a "
                "critical/repeating error), as opposed to routine or "
                "informational output?"
            ),
            criteria=CRITERIA,
        )
        for key in keys
    }
    async with semaphore:
        response = await client.system_one(state=state, questions=questions)
    return [
        (line_no, text)
        for key, (line_no, text) in zip(keys, batch)
        if response.nouls[key].noul > threshold
    ]


async def label_logs(log_path, output_path, batch_size, concurrency, threshold):
    semaphore = asyncio.Semaphore(concurrency)
    retry = RetryPolicy(max_retries=5)

    flagged_by_line = {}
    batches = list(read_batches(log_path, batch_size))
    total = len(batches)

    async with AsyncTypeSafeClient(retry=retry) as client:
        tasks = [
            asyncio.create_task(process_batch(client, semaphore, batch, threshold)) for batch in batches
        ]
        done = 0
        for task in asyncio.as_completed(tasks):
            done += 1
            try:
                for line_no, text in await task:
                    flagged_by_line[line_no] = text
            except TypeSafeAPIError as error:
                print(f"warning: skipping a batch after API error: {error}", file=sys.stderr)
            if done % 50 == 0 or done == total:
                print(f"processed {done}/{total} batches", file=sys.stderr)

    with open(output_path, "w", encoding="utf-8") as out:
        for line_no in sorted(flagged_by_line):
            out.write(flagged_by_line[line_no] + "\n")

    print(f"flagged {len(flagged_by_line)} line(s) -> {output_path}", file=sys.stderr)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_file", help="Path to the log file, one entry per line.")
    parser.add_argument("-o", "--output", default="flagged.txt", help="Path to write flagged lines to.")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="Log lines per API request.")
    parser.add_argument("--concurrency", type=int, default=CONCURRENCY, help="Concurrent requests in flight.")
    parser.add_argument("--threshold", type=float, default=THRESHOLD, help="Noul probability cutoff to flag a line.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(label_logs(args.log_file, args.output, args.batch_size, args.concurrency, args.threshold))
