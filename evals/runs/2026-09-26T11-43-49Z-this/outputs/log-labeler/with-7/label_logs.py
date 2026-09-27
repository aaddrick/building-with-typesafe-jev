#!/usr/bin/env python3
"""Flag application log lines that need an on-call engineer, using typesafe.ai's Jev model.

Requires TYPESAFE_API_KEY to be set. Install the SDK with:
    pip install typesafe-sdk
"""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor

from typesafe_sdk import Noul, TypeSafeClient

# Tune these together: they were fit against jev-1.13.0.
MODEL = "jev-1.13.0"
BATCH_SIZE = 50  # log lines per request; keeps state+questions well under the 64k token limit
MAX_WORKERS = 8  # shared-key rate limit ceiling before 429s become frequent
NOUL_THRESHOLD = 0.7

QUESTION_TEMPLATE = (
    "Does `lines[{i}]` describe something serious enough that an on-call "
    "engineer needs to be paged right now -- e.g. a crash, an outage, data "
    "loss, a security breach, a service that is down, or an unhandled "
    "exception in a critical path? Routine info/debug logs, expected "
    "warnings, and successful requests do not qualify."
)


def build_questions(n: int) -> dict:
    return {f"line_{i}": Noul(instructions=QUESTION_TEMPLATE.format(i=i)) for i in range(n)}


def label_batch(client: TypeSafeClient, batch: list[str]) -> list[bool]:
    response = client.system_one(
        state={"lines": batch},
        questions=build_questions(len(batch)),
        model=MODEL,
    )
    return [response.nouls[f"line_{i}"].noul > NOUL_THRESHOLD for i in range(len(batch))]


def chunked(seq: list, size: int):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_file", help="path to the log file, one entry per line")
    parser.add_argument("-o", "--output", default="flagged.txt", help="where to write flagged lines")
    args = parser.parse_args()

    with open(args.log_file, "r", encoding="utf-8", errors="replace") as f:
        lines = [line.rstrip("\n") for line in f]

    batches = list(chunked(lines, BATCH_SIZE))
    flagged_count = 0

    with TypeSafeClient() as client, open(args.output, "w", encoding="utf-8") as out:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            results = pool.map(lambda b: label_batch(client, b), batches)
            for batch, flags in zip(batches, results):
                for line, flagged in zip(batch, flags):
                    if flagged:
                        out.write(line + "\n")
                        flagged_count += 1

    print(f"{len(lines)} lines processed, {flagged_count} flagged -> {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
