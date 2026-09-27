#!/usr/bin/env python3
"""Flag log lines that need on-call attention using TypeSafe's Jev model."""

import argparse
import asyncio
import sys

from typesafe_sdk import (
    AsyncTypeSafeClient,
    Noul,
    NoulCriteria,
    RetryPolicy,
    TypeSafeAPIError,
)

MODEL = "jev-latest"
QUESTION = (
    "Does line `lines.{line_id}` describe an application problem (e.g. an error, "
    "exception, crash, resource exhaustion, security incident, or service outage) "
    "severe enough that an on-call engineer should be paged?"
)
CRITERIA = NoulCriteria(
    true="The line reports a failure or degraded condition that needs human intervention.",
    false="The line is routine or informational and does not need paging anyone.",
)


def line_id(i: int) -> str:
    return f"L{i:06d}"


def chunk(items, size):
    for i in range(0, len(items), size):
        yield items[i : i + size]


async def score_batch(client, semaphore, batch):
    # Batching many lines into one shared `state` document and asking one Noul
    # per line is far cheaper/faster than one request per line: cost is
    # dominated by the shared state, and Noul questions evaluate in parallel.
    ids = [line_id(i) for i, _ in batch]
    state = {"lines": {lid: text for lid, (_, text) in zip(ids, batch)}}
    questions = {
        lid: Noul(instructions=QUESTION.format(line_id=lid), criteria=CRITERIA)
        for lid in ids
    }
    async with semaphore:
        response = await client.system_one(state=state, questions=questions, model=MODEL)
    return {i: response.answers[lid].noul for lid, (i, _) in zip(ids, batch)}


async def label(lines, batch_size, concurrency):
    retry = RetryPolicy(max_retries=3, timeout=30.0)
    scores: dict[int, float] = {}
    async with AsyncTypeSafeClient(retry=retry) as client:
        semaphore = asyncio.Semaphore(concurrency)
        indexed = list(enumerate(lines))
        tasks = [
            asyncio.create_task(score_batch(client, semaphore, batch))
            for batch in chunk(indexed, batch_size)
        ]
        for task in asyncio.as_completed(tasks):
            try:
                scores.update(await task)
            except TypeSafeAPIError as error:
                print(
                    f"warning: batch failed after retries: {error.status} {error.request_id}",
                    file=sys.stderr,
                )
    return scores


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logfile")
    parser.add_argument("-o", "--output", default="flagged.txt")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=20)
    args = parser.parse_args()

    with open(args.logfile, encoding="utf-8", errors="replace") as f:
        lines = [line.rstrip("\n") for line in f]

    scores = asyncio.run(label(lines, args.batch_size, args.concurrency))

    flagged_count = 0
    with open(args.output, "w", encoding="utf-8") as out:
        for i, line in enumerate(lines):
            if scores.get(i, 0.0) >= args.threshold:
                out.write(line + "\n")
                flagged_count += 1

    print(f"{flagged_count}/{len(lines)} lines flagged -> {args.output}")


if __name__ == "__main__":
    main()
