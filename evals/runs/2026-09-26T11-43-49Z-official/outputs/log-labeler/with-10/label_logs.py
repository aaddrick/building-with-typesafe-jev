#!/usr/bin/env python3
"""Flag application log lines that need on-call engineer attention using typesafe.ai's Jev model."""

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

# Lines per API call. One Noul question is asked per line, so this bounds both
# the state size and the question count of a single request.
CHUNK_SIZE = 100
# In-flight requests at once. 50k lines / CHUNK_SIZE chunks, throttled so we
# stay well clear of per-account rate limits while still parallelizing.
CONCURRENCY = 20
# Probability above which a line is considered "needs on-call attention".
THRESHOLD = 0.5

INSTRUCTIONS_TEMPLATE = (
    "Does the log line at `lines[{i}]` describe a problem serious enough that an "
    "on-call engineer needs to be paged right now (e.g. crash, outage, unhandled "
    "exception, data loss, security incident, dependency/downstream failure)?"
)
CRITERIA = NoulCriteria(
    true=(
        "An error or failure that is degrading or breaking production for users, "
        "or a security incident."
    ),
    false=(
        "Routine, informational, debug, or warning output that does not require "
        "an immediate human response."
    ),
)


def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


async def classify_chunk(client, semaphore, lines):
    questions = {
        f"L{i}": Noul(instructions=INSTRUCTIONS_TEMPLATE.format(i=i), criteria=CRITERIA)
        for i in range(len(lines))
    }
    async with semaphore:
        try:
            response = await client.system_one(state={"lines": lines}, questions=questions)
        except TypeSafeAPIError as exc:
            print(f"warning: chunk of {len(lines)} lines failed ({exc}); skipping", file=sys.stderr)
            return [False] * len(lines)
    return [response.answers[f"L{i}"].noul > THRESHOLD for i in range(len(lines))]


async def label_lines(lines):
    semaphore = asyncio.Semaphore(CONCURRENCY)
    async with AsyncTypeSafeClient(retry=RetryPolicy(max_retries=5)) as client:
        tasks = [classify_chunk(client, semaphore, batch) for batch in chunked(lines, CHUNK_SIZE)]
        results = await asyncio.gather(*tasks)
    flags = []
    for batch_flags in results:
        flags.extend(batch_flags)
    return flags


def main():
    parser = argparse.ArgumentParser(description="Flag log lines needing on-call attention.")
    parser.add_argument("logfile", help="Path to the application log file")
    parser.add_argument("-o", "--output", default="flagged.txt", help="Output path for flagged lines")
    args = parser.parse_args()

    with open(args.logfile, encoding="utf-8", errors="replace") as f:
        lines = [line.rstrip("\n") for line in f]

    # Skip blank lines: nothing for the model to judge, and they're never flaggable.
    non_blank_indices = [i for i, line in enumerate(lines) if line.strip()]
    non_blank_lines = [lines[i] for i in non_blank_indices]

    flags = asyncio.run(label_lines(non_blank_lines))

    flagged_lines = [lines[i] for i, flagged in zip(non_blank_indices, flags) if flagged]

    with open(args.output, "w", encoding="utf-8") as f:
        for line in flagged_lines:
            f.write(line + "\n")

    print(f"Flagged {len(flagged_lines)} / {len(lines)} lines -> {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
