#!/usr/bin/env python3
"""Flag log lines that need on-call engineer attention using typesafe.ai's Jev model.

Usage:
    python label_logs.py <log_file> [--output flagged.txt] [--chunk-size 25]
                          [--concurrency 20] [--threshold 0.5] [--model jev-latest]

Requires TYPESAFE_API_KEY to be set in the environment and `typesafe-sdk` installed
(`pip install typesafe-sdk`).
"""

import argparse
import asyncio
import sys

from typesafe_sdk import AsyncTypeSafeClient, Noul, NoulCriteria, RetryPolicy

ON_CALL_CRITERIA = NoulCriteria(
    true=(
        "The line reports an active failure needing immediate attention: an "
        "unhandled exception or stack trace, a crash, a service outage or failed "
        "health check, a dependency that is down or unreachable, a security or "
        "data-integrity incident, or resource exhaustion (OOM, disk full, etc.)."
    ),
    false=(
        "The line is informational, a routine/expected warning, a successful "
        "operation, or otherwise does not require paging anyone."
    ),
)


def load_lines(path: str) -> list[str]:
    with open(path, encoding="utf-8", errors="replace") as f:
        return [line.rstrip("\n") for line in f]


def chunked(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


async def classify_chunk(
    client: AsyncTypeSafeClient,
    sem: asyncio.Semaphore,
    model: str,
    chunk: list[tuple[int, str]],
) -> list[tuple[int, str, float]]:
    """Ask one Noul question per line in the chunk, in a single API call."""
    non_blank = [(i, idx, line) for i, (idx, line) in enumerate(chunk) if line.strip()]
    if not non_blank:
        return []

    state = {"lines": {str(i): line for i, _, line in non_blank}}
    questions = {
        f"l{i}": Noul(
            instructions=(
                f'Look only at state.lines["{i}"]. Does that single log line '
                "describe a problem serious enough that an on-call engineer "
                "should be paged right now?"
            ),
            criteria=ON_CALL_CRITERIA,
        )
        for i, _, _ in non_blank
    }

    async with sem:
        response = await client.system_one(model=model, state=state, questions=questions)

    return [
        (idx, line, response.answers[f"l{i}"].noul) for i, idx, line in non_blank
    ]


async def run(args: argparse.Namespace) -> None:
    lines = load_lines(args.log_file)
    indexed_lines = list(enumerate(lines))

    retry = RetryPolicy(max_retries=5)
    flagged: dict[int, str] = {}
    processed = 0
    total = len(indexed_lines)
    sem = asyncio.Semaphore(args.concurrency)

    async with AsyncTypeSafeClient(retry=retry) as client:
        tasks = [
            asyncio.create_task(classify_chunk(client, sem, args.model, chunk))
            for chunk in chunked(indexed_lines, args.chunk_size)
        ]
        for task in asyncio.as_completed(tasks):
            try:
                results = await task
            except Exception as exc:  # noqa: BLE001 - report and keep going
                print(f"warning: a chunk failed after retries: {exc}", file=sys.stderr)
                continue
            for idx, line, score in results:
                if score >= args.threshold:
                    flagged[idx] = line
            processed += len(results)
            print(f"\r{processed}/{total} lines classified...", end="", file=sys.stderr)

    print(file=sys.stderr)
    with open(args.output, "w", encoding="utf-8") as f:
        for idx in sorted(flagged):
            f.write(flagged[idx] + "\n")

    print(f"Flagged {len(flagged)}/{total} lines -> {args.output}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_file", help="Path to the log file (one entry per line)")
    parser.add_argument("--output", default="flagged.txt", help="Where to write flagged lines")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=25,
        help="Log lines per API call (batched as separate questions to cut cost/latency)",
    )
    parser.add_argument(
        "--concurrency", type=int, default=20, help="Max concurrent API calls"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Minimum on-call probability (0-1) required to flag a line",
    )
    parser.add_argument("--model", default="jev-latest", help="Jev model to use")
    args = parser.parse_args()

    asyncio.run(run(args))


if __name__ == "__main__":
    main()
