#!/usr/bin/env python3
"""Flag log lines that need on-call engineer attention using typesafe.ai's Jev model.

Requires: pip install typesafe-sdk
Requires: TYPESAFE_API_KEY environment variable set to a valid API key.
"""

import argparse
import asyncio
import sys

from typesafe_sdk import AsyncTypeSafeClient, Noul, NoulCriteria, RetryPolicy

INSTRUCTIONS = (
    "Does this log line indicate a problem serious enough that an on-call "
    "engineer should be paged or notified right now?"
)

CRITERIA = NoulCriteria(
    true=(
        "The line reports a crash, unhandled exception, service outage, "
        "failed health check, data loss, security incident, or another "
        "condition that needs a human to act immediately."
    ),
    false=(
        "The line is routine info/debug output, an expected warning, or "
        "anything else that does not need immediate human attention."
    ),
)


async def classify(client, semaphore, index, line):
    async with semaphore:
        try:
            response = await client.system_one(
                state=line,
                questions={"needs_oncall": Noul(instructions=INSTRUCTIONS, criteria=CRITERIA)},
            )
            score = response.answers["needs_oncall"].noul
            return index, score >= 0.5, None
        except Exception as exc:  # one bad line shouldn't kill a 50k-line run
            return index, False, exc


async def run(input_path, output_path, concurrency, model):
    with open(input_path, "r", encoding="utf-8", errors="replace") as f:
        lines = [line.rstrip("\n") for line in f]

    semaphore = asyncio.Semaphore(concurrency)

    async with AsyncTypeSafeClient(
        model=model,
        retry=RetryPolicy(max_retries=5, timeout=30.0),
    ) as client:
        tasks = [
            asyncio.create_task(classify(client, semaphore, i, line))
            for i, line in enumerate(lines)
            if line.strip()
        ]

        total = len(tasks)
        done = 0
        errors = 0
        flagged = {}

        for coro in asyncio.as_completed(tasks):
            index, is_flagged, exc = await coro
            flagged[index] = is_flagged
            if exc is not None:
                errors += 1
                print(f"warning: line {index + 1} failed classification: {exc}", file=sys.stderr)
            done += 1
            if done % 500 == 0 or done == total:
                print(f"processed {done}/{total} lines", file=sys.stderr)

    flagged_lines = [lines[i] for i in sorted(flagged) if flagged[i]]

    with open(output_path, "w", encoding="utf-8") as f:
        for line in flagged_lines:
            f.write(line + "\n")

    print(
        f"done: {len(flagged_lines)} flagged out of {total} lines "
        f"({errors} classification errors)",
        file=sys.stderr,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logfile", help="Path to the input log file")
    parser.add_argument(
        "-o", "--output", default="flagged.txt", help="Path to write flagged lines to"
    )
    parser.add_argument(
        "-c",
        "--concurrency",
        type=int,
        default=25,
        help="Max concurrent requests to the Jev API (tune based on your rate limit)",
    )
    parser.add_argument("--model", default="jev-latest", help="Jev model to use")
    args = parser.parse_args()

    asyncio.run(run(args.logfile, args.output, args.concurrency, args.model))


if __name__ == "__main__":
    main()
