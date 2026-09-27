#!/usr/bin/env python3
"""Flag log lines that need an on-call engineer, using TypeSafe's Jev model.

Usage:
    python label_logs.py app.log [-o flagged.txt] [--batch-size 25] [--concurrency 20]

Lines are sent to Jev in batches (many lines share one request as independent
Noul questions over shared state) and batches run concurrently, so a 50k-line
file finishes in a handful of round trips instead of one call per line.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time

from typesafe_sdk import AsyncTypeSafeClient, Noul

MODEL = "jev-latest"

CRITERIA = {
    "true": (
        "The line reports a crash, unhandled exception, service outage, data "
        "loss or corruption, security incident, cascading failure, or another "
        "critical error that is actively breaking functionality right now and "
        "needs a human to step in."
    ),
    "false": (
        "The line is routine informational or debug output, an expected or "
        "already-handled warning, a successful operation, or a minor issue "
        "that does not need immediate human attention."
    ),
}


def read_lines(path: str) -> list[tuple[int, str]]:
    with open(path, encoding="utf-8", errors="replace") as f:
        raw = [line.rstrip("\n").rstrip("\r") for line in f]
    return [(i, text) for i, text in enumerate(raw) if text.strip()]


def chunk(items: list[tuple[int, str]], size: int) -> list[list[tuple[int, str]]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


async def label_batch(
    client: AsyncTypeSafeClient,
    batch: list[tuple[int, str]],
    threshold: float,
) -> list[tuple[int, str]]:
    state = {"lines": [text for _, text in batch]}
    questions = {
        f"line_{i}": Noul(
            instructions=(
                f"Consider the application log line at `lines[{i}]`. Does it "
                "indicate a problem serious enough that an on-call engineer "
                "should be paged right now?"
            ),
            criteria=CRITERIA,
        )
        for i in range(len(batch))
    }

    try:
        result = await client.system_one(state=state, questions=questions, model=MODEL)
    except Exception as exc:  # noqa: BLE001 - conservative fallback below
        print(
            f"warning: batch starting at line {batch[0][0] + 1} failed ({exc}); "
            "flagging its lines for manual review",
            file=sys.stderr,
        )
        return list(batch)

    flagged = []
    for i, (line_no, text) in enumerate(batch):
        if result.nouls[f"line_{i}"].noul >= threshold:
            flagged.append((line_no, text))
    return flagged


async def run(
    input_path: str,
    output_path: str,
    batch_size: int,
    concurrency: int,
    threshold: float,
) -> None:
    lines = read_lines(input_path)
    if not lines:
        open(output_path, "w").close()
        print("No non-empty lines to process.")
        return

    batches = chunk(lines, batch_size)
    semaphore = asyncio.Semaphore(concurrency)
    done = 0
    start = time.monotonic()

    async with AsyncTypeSafeClient() as client:

        async def worker(batch: list[tuple[int, str]]) -> list[tuple[int, str]]:
            nonlocal done
            async with semaphore:
                result = await label_batch(client, batch, threshold)
            done += 1
            print(
                f"\r{done}/{len(batches)} batches processed "
                f"({done * batch_size} / {len(lines)} lines)",
                end="",
                file=sys.stderr,
            )
            return result

        results = await asyncio.gather(*(worker(b) for b in batches))

    print(file=sys.stderr)

    flagged = [pair for batch_result in results for pair in batch_result]
    flagged.sort(key=lambda pair: pair[0])

    with open(output_path, "w", encoding="utf-8") as f:
        for _, text in flagged:
            f.write(text + "\n")

    elapsed = time.monotonic() - start
    print(
        f"Processed {len(lines)} lines in {elapsed:.1f}s, "
        f"flagged {len(flagged)} -> {output_path}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Path to the log file, one entry per line")
    parser.add_argument("-o", "--output", default="flagged.txt", help="Output file for flagged lines")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=25,
        help="Log lines per Jev request (default: 25)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=20,
        help="Number of Jev requests to run concurrently (default: 20)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.6,
        help="Minimum on-call probability to flag a line (default: 0.6)",
    )
    args = parser.parse_args()

    asyncio.run(
        run(args.input, args.output, args.batch_size, args.concurrency, args.threshold)
    )


if __name__ == "__main__":
    main()
