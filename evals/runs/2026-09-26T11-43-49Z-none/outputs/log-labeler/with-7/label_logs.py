#!/usr/bin/env python3
"""Flag log lines that need on-call attention using typesafe.ai's Jev model.

Usage:
    pip install typesafe-sdk
    export TYPESAFE_API_KEY=...
    python label_logs.py app.log
"""

import asyncio
import sys

from typesafe_sdk import AsyncTypeSafeClient, Noul

# Jev bills/latency-bounds per request mostly by the shared "state" payload,
# not by question count, so grouping many lines into one request (and asking
# one Noul question per line) is far cheaper and faster than one request per
# line. Concurrency across batches then parallelizes the remaining round trips.
BATCH_SIZE = 50
CONCURRENCY = 20
NOUL_THRESHOLD = 0.5

INSTRUCTIONS = (
    "state[{i}] is one line from an application log. Does it indicate a "
    "problem serious enough that an on-call engineer should be paged right "
    "now (e.g. crash, outage, data loss, security incident, repeated/fatal "
    "errors) as opposed to routine info/debug/warning noise?"
)


async def classify_batch(client: AsyncTypeSafeClient, lines: list[str]) -> list[str]:
    questions = {
        str(i): Noul(instructions=INSTRUCTIONS.format(i=i)) for i in range(len(lines))
    }
    response = await client.system_one(state=lines, questions=questions)
    return [
        line
        for i, line in enumerate(lines)
        if response.answers[str(i)].noul >= NOUL_THRESHOLD
    ]


async def run(input_path: str, output_path: str) -> None:
    with open(input_path) as f:
        lines = [line.rstrip("\n") for line in f]

    batches = [lines[i : i + BATCH_SIZE] for i in range(0, len(lines), BATCH_SIZE)]
    results: list[list[str] | None] = [None] * len(batches)
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async with AsyncTypeSafeClient() as client:

        async def worker(index: int, batch: list[str]) -> None:
            async with semaphore:
                results[index] = await classify_batch(client, batch)

        await asyncio.gather(*(worker(i, b) for i, b in enumerate(batches)))

    with open(output_path, "w") as out:
        for flagged in results:
            for line in flagged:
                out.write(line + "\n")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: label_logs.py <logfile>", file=sys.stderr)
        raise SystemExit(1)
    asyncio.run(run(sys.argv[1], "flagged.txt"))


if __name__ == "__main__":
    main()
