#!/usr/bin/env python3
"""Flag log lines that need on-call attention using TypeSafe's Jev model.

Requires: pip install typesafe-sdk
Requires: TYPESAFE_API_KEY set in the environment.
"""

import argparse
import asyncio
import sys

from typesafe_sdk import (
    AsyncTypeSafeClient,
    Noul,
    NoulCriteria,
    RetryPolicy,
    TypeSafeError,
)

QUESTIONS = {
    "needs_oncall": Noul(
        instructions=(
            "Does this application log line indicate a problem serious enough "
            "that an on-call engineer should be paged right now?"
        ),
        criteria=NoulCriteria(
            true=(
                "Crashes, unhandled exceptions, service outages, failed health "
                "checks, data loss/corruption, security incidents, or other "
                "conditions requiring immediate human intervention."
            ),
            false=(
                "Routine informational, debug, or warning output, and any "
                "expected/handled condition that does not require a human "
                "to act immediately."
            ),
        ),
    ),
}


async def classify_line(client, semaphore, index, line):
    async with semaphore:
        try:
            response = await client.system_one(
                model="jev-latest",
                state=line,
                questions=QUESTIONS,
            )
            return index, response.answers["needs_oncall"].noul
        except TypeSafeError as error:
            print(f"warning: line {index + 1}: {error}", file=sys.stderr)
            return index, None


async def label_logs(input_path, output_path, concurrency, threshold):
    with open(input_path, encoding="utf-8", errors="replace") as f:
        lines = [line.rstrip("\n") for line in f]

    semaphore = asyncio.Semaphore(concurrency)
    retry = RetryPolicy(max_retries=5)

    async with AsyncTypeSafeClient(retry=retry) as client:
        tasks = [
            asyncio.create_task(classify_line(client, semaphore, i, line))
            for i, line in enumerate(lines)
            if line.strip()
        ]

        scores = {}
        total = len(tasks)
        done = 0
        for coro in asyncio.as_completed(tasks):
            index, noul = await coro
            scores[index] = noul
            done += 1
            if done % 1000 == 0 or done == total:
                print(f"classified {done}/{total} lines", file=sys.stderr)

    flagged = [
        lines[i]
        for i in range(len(lines))
        if scores.get(i) is not None and scores[i] >= threshold
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        for line in flagged:
            f.write(line + "\n")

    print(f"flagged {len(flagged)}/{len(lines)} lines -> {output_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Flag log lines that need on-call attention using TypeSafe's Jev model."
    )
    parser.add_argument("input", help="Path to the log file (one entry per line)")
    parser.add_argument("--output", default="flagged.txt", help="Path to write flagged lines")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=50,
        help="Number of concurrent Jev requests (tune to your account's rate limit)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Minimum probability (0-1) to flag a line as needing on-call attention",
    )
    args = parser.parse_args()

    asyncio.run(label_logs(args.input, args.output, args.concurrency, args.threshold))


if __name__ == "__main__":
    main()
