#!/usr/bin/env python3
"""Flag log lines that need on-call attention using typesafe.ai's Jev model.

Reads a log file, sends the lines to Jev in batches (many Noul questions
per request, since request cost/latency is dominated by the state payload
rather than the number of questions asked against it), and writes every
line Jev flags as needing a human to `flagged.txt`, in original order.
"""

import argparse
import asyncio
import os
import sys

from typesafe_sdk import AsyncTypeSafeClient, Noul, TypeSafeError

ON_CALL_INSTRUCTIONS = (
    "In the JSON array given as state, look only at the entry whose \"index\" "
    "field is {i}. Does that log line indicate something serious enough that "
    "an on-call engineer should be paged right now -- e.g. an unhandled "
    "exception or stack trace, a crash, a service outage, a failed health "
    "check, a security incident, or data loss? Routine info/debug/access "
    "lines and expected, already-handled warnings are false."
)

ON_CALL_CRITERIA = {
    "true": "The line reports a crash, unhandled exception, outage, failed "
    "health check, security incident, or data loss that needs immediate "
    "human attention.",
    "false": "The line is routine info/debug output, an expected/handled "
    "warning, or otherwise does not require paging anyone.",
}


def read_lines(path):
    with open(path, "r", errors="replace") as f:
        return [line.rstrip("\r\n") for line in f]


def chunks(indexed_lines, size):
    for i in range(0, len(indexed_lines), size):
        yield indexed_lines[i : i + size]


async def classify_batch(client, semaphore, batch, threshold, model):
    """batch: list of (original_index, line). Returns {index: bool}."""
    state = [{"index": idx, "line": line} for idx, line in batch]
    questions = {
        str(idx): Noul(
            instructions=ON_CALL_INSTRUCTIONS.format(i=idx),
            criteria=ON_CALL_CRITERIA,
        )
        for idx, _ in batch
    }

    async with semaphore:
        try:
            result = await client.system_one(
                state=state, questions=questions, model=model
            )
        except TypeSafeError as exc:
            print(
                f"warning: batch starting at line {batch[0][0]} failed "
                f"({exc}); flagging its lines for manual review",
                file=sys.stderr,
            )
            return {idx: True for idx, _ in batch}

    flagged = {}
    for idx, _ in batch:
        answer = result.nouls.get(str(idx))
        flagged[idx] = answer is not None and answer.noul >= threshold
    return flagged


async def run(args):
    lines = read_lines(args.input)
    if not lines:
        open(args.output, "w").close()
        return

    # Blank/whitespace-only lines can never need paging; skip calling the
    # model for them so batches only spend budget on real content.
    indexed = [(i, line) for i, line in enumerate(lines) if line.strip()]

    semaphore = asyncio.Semaphore(args.concurrency)
    flagged_by_index = {}

    async with AsyncTypeSafeClient() as client:
        tasks = [
            asyncio.create_task(
                classify_batch(client, semaphore, batch, args.threshold, args.model)
            )
            for batch in chunks(indexed, args.batch_size)
        ]
        for coro in asyncio.as_completed(tasks):
            flagged_by_index.update(await coro)

    with open(args.output, "w") as f:
        for i, line in enumerate(lines):
            if flagged_by_index.get(i):
                f.write(line + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="path to the log file to scan")
    parser.add_argument(
        "-o", "--output", default="flagged.txt", help="where to write flagged lines"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=25,
        help="log lines bundled into a single Jev request",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="number of batch requests in flight at once",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Noul score at/above which a line is flagged",
    )
    parser.add_argument("--model", default="jev-latest", help="Jev model name")
    args = parser.parse_args()

    if not os.environ.get("TYPESAFE_API_KEY"):
        sys.exit("error: TYPESAFE_API_KEY environment variable is not set")

    asyncio.run(run(args))


if __name__ == "__main__":
    main()
