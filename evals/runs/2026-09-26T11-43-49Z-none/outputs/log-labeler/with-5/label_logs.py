#!/usr/bin/env python3
"""Flag log lines that need on-call attention using typesafe.ai's Jev model.

Requires the TYPESAFE_API_KEY environment variable and the typesafe-sdk
package (`pip install typesafe-sdk`).
"""

import argparse
import asyncio
import sys

from typesafe_sdk import AsyncTypeSafeClient, Noul

ON_CALL_QUESTION = "on_call"
ON_CALL_INSTRUCTIONS = (
    "This log line indicates a problem serious enough that an on-call "
    "engineer should be paged right now (e.g. an error, exception, crash, "
    "service outage, failed health check, or other critical failure). "
    "Routine informational or debug lines do not need on-call attention."
)


async def classify_line(client, semaphore, index, line, model):
    async with semaphore:
        try:
            response = await client.system_one(
                state=line,
                model=model,
                questions={
                    ON_CALL_QUESTION: Noul(instructions=ON_CALL_INSTRUCTIONS),
                },
            )
            probability = response.answers[ON_CALL_QUESTION].noul
            return index, line, probability, None
        except Exception as exc:  # noqa: BLE001 - report and keep going
            return index, line, None, exc


async def run(input_path, output_path, model, concurrency, threshold):
    with open(input_path, "r", encoding="utf-8", errors="replace") as f:
        lines = [line.rstrip("\n") for line in f]

    semaphore = asyncio.Semaphore(concurrency)
    errors = []

    async with AsyncTypeSafeClient() as client:
        tasks = [
            classify_line(client, semaphore, i, line, model)
            for i, line in enumerate(lines)
            if line.strip()
        ]
        results = [None] * len(lines)
        completed = 0
        total = len(tasks)
        for coro in asyncio.as_completed(tasks):
            index, line, probability, error = await coro
            results[index] = (line, probability, error)
            if error is not None:
                errors.append((index, line, error))
            completed += 1
            if completed % 500 == 0 or completed == total:
                print(f"Classified {completed}/{total} lines", file=sys.stderr)

    flagged = [
        line
        for entry in results
        if entry is not None
        for line, probability, error in [entry]
        if error is None and probability is not None and probability >= threshold
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        for line in flagged:
            f.write(line + "\n")

    print(f"Flagged {len(flagged)} of {len(lines)} lines -> {output_path}", file=sys.stderr)
    if errors:
        print(f"{len(errors)} lines failed classification, e.g.: {errors[0][2]}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Path to the log file to classify")
    parser.add_argument(
        "-o", "--output", default="flagged.txt", help="Path to write flagged lines to"
    )
    parser.add_argument("--model", default="jev-latest", help="Jev model to use")
    parser.add_argument(
        "--concurrency", type=int, default=50, help="Max in-flight requests"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Minimum on-call probability (0-1) required to flag a line",
    )
    args = parser.parse_args()

    asyncio.run(
        run(args.input, args.output, args.model, args.concurrency, args.threshold)
    )


if __name__ == "__main__":
    main()
