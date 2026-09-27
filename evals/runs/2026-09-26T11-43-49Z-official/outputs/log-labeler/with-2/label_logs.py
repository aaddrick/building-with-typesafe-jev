#!/usr/bin/env python3
"""Flag log lines that need an on-call engineer using typesafe.ai's Jev model.

Requires:
    pip install typesafe-sdk
    export TYPESAFE_API_KEY=...

Usage:
    python label_logs.py app.log
    python label_logs.py app.log --output flagged.txt --concurrency 20
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from typesafe_sdk import AsyncTypeSafeClient, Noul, NoulCriteria, RetryPolicy

# Jev's context budget is 64k tokens per request (state + all questions combined).
# Each batched question carries one log line, so batches are capped on both line
# count and total characters to stay well under that budget even when some lines
# (stack traces, JSON blobs) are much longer than average.
DEFAULT_BATCH_SIZE = 300
MAX_BATCH_CHARS = 80_000

ON_CALL_QUESTION = (
    "Does this application log line describe a problem severe enough that a "
    "human on-call engineer should be paged right now - for example a crash, "
    "service outage, data loss or corruption, security incident, or other "
    "production-impacting failure?"
)
ON_CALL_CRITERIA = NoulCriteria(
    true=(
        "The line reports a critical failure, unhandled exception, outage, "
        "data loss or corruption, security incident, or other severe issue "
        "that needs immediate human attention."
    ),
    false=(
        "The line is routine informational or debug output, an expected or "
        "already-handled event, or a minor warning that does not need "
        "immediate action."
    ),
)
STATE_CONTEXT = (
    "You are reviewing lines from a production application log to decide "
    "which ones need to page an on-call engineer immediately."
)


def read_lines(path: str) -> list[tuple[int, str]]:
    """Return (original_line_number, text) pairs for non-blank lines."""
    with open(path, encoding="utf-8", errors="replace") as f:
        return [
            (i, line.rstrip("\n"))
            for i, line in enumerate(f, start=1)
            if line.strip()
        ]


def make_batches(
    lines: list[tuple[int, str]], batch_size: int, max_chars: int
) -> list[list[tuple[int, str]]]:
    batches: list[list[tuple[int, str]]] = []
    current: list[tuple[int, str]] = []
    current_chars = 0
    for entry in lines:
        line_chars = len(entry[1])
        if current and (
            len(current) >= batch_size or current_chars + line_chars > max_chars
        ):
            batches.append(current)
            current = []
            current_chars = 0
        current.append(entry)
        current_chars += line_chars
    if current:
        batches.append(current)
    return batches


async def label_batch(
    client: AsyncTypeSafeClient,
    batch: list[tuple[int, str]],
    threshold: float,
) -> list[tuple[int, str]]:
    """Ask one Noul question per line in a single request; return flagged (line_no, text)."""
    questions = {
        f"q{i}": Noul(
            instructions={"log_line": text, "question": ON_CALL_QUESTION},
            criteria=ON_CALL_CRITERIA,
        )
        for i, (_, text) in enumerate(batch)
    }
    try:
        response = await client.system_one(state=STATE_CONTEXT, questions=questions)
    except Exception as exc:
        if len(batch) == 1:
            print(f"warning: giving up on line {batch[0][0]}: {exc}", file=sys.stderr)
            return []
        # Something about this batch (e.g. a request too large) failed; split
        # it and retry the halves independently rather than losing the batch.
        mid = len(batch) // 2
        left, right = await asyncio.gather(
            label_batch(client, batch[:mid], threshold),
            label_batch(client, batch[mid:], threshold),
        )
        return left + right

    flagged = []
    for i, (line_no, text) in enumerate(batch):
        if response.nouls[f"q{i}"].noul > threshold:
            flagged.append((line_no, text))
    return flagged


async def run(
    input_path: str,
    output_path: str,
    batch_size: int,
    max_chars: int,
    concurrency: int,
    threshold: float,
    model: str,
) -> None:
    lines = read_lines(input_path)
    batches = make_batches(lines, batch_size, max_chars)
    print(f"{len(lines)} lines, {len(batches)} batches", file=sys.stderr)

    semaphore = asyncio.Semaphore(concurrency)
    done = 0

    async def bounded(batch: list[tuple[int, str]]) -> list[tuple[int, str]]:
        nonlocal done
        async with semaphore:
            result = await label_batch(client, batch, threshold)
        done += 1
        if done % 10 == 0 or done == len(batches):
            print(f"processed {done}/{len(batches)} batches", file=sys.stderr)
        return result

    async with AsyncTypeSafeClient(
        model=model, retry=RetryPolicy(max_retries=4)
    ) as client:
        results = await asyncio.gather(*(bounded(b) for b in batches))

    flagged = [entry for batch_result in results for entry in batch_result]
    flagged.sort(key=lambda entry: entry[0])

    with open(output_path, "w", encoding="utf-8") as f:
        for _, text in flagged:
            f.write(text + "\n")

    print(f"flagged {len(flagged)}/{len(lines)} lines -> {output_path}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Path to the log file, one entry per line")
    parser.add_argument("--output", default="flagged.txt", help="Path to write flagged lines")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--max-batch-chars", type=int, default=MAX_BATCH_CHARS)
    parser.add_argument("--concurrency", type=int, default=20, help="Concurrent requests")
    parser.add_argument("--threshold", type=float, default=0.5, help="Noul cutoff for flagging")
    parser.add_argument("--model", default="jev-latest")
    args = parser.parse_args()

    asyncio.run(
        run(
            args.input,
            args.output,
            args.batch_size,
            args.max_batch_chars,
            args.concurrency,
            args.threshold,
            args.model,
        )
    )


if __name__ == "__main__":
    main()
