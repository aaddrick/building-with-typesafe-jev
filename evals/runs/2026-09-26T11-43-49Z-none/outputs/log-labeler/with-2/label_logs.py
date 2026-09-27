#!/usr/bin/env python3
"""Flag log lines that need on-call engineer attention using typesafe.ai's Jev model.

Lines are grouped into chunks and sent as a single shared `state` per API call,
with one Noul (yes/no) question per line. Since Jev's cost/latency for a batched
call is dominated by the shared state rather than the question count, this is far
cheaper and faster than one API call per line. Chunks are then processed
concurrently to keep throughput high across a large file.
"""

import argparse
import asyncio
import sys

from typesafe_sdk import AsyncTypeSafeClient, Noul

ONCALL_CRITERIA = {
    "true": (
        "The log entry indicates a problem that needs immediate attention from an "
        "on-call engineer: errors, exceptions, stack traces, crashes, panics, "
        "timeouts, failed health checks, service outages, security incidents, or "
        "data loss/corruption."
    ),
    "false": (
        "The log entry is routine or informational and does not require paging "
        "anyone (e.g. normal request logs, debug output, successful operations)."
    ),
}


def build_questions(lines: list[str]) -> dict[str, Noul]:
    return {
        f"line_{i}": Noul(
            instructions=f"Does the log entry at index {i} in `log_lines` need on-call engineer attention?",
            criteria=ONCALL_CRITERIA,
        )
        for i in range(len(lines))
    }


async def classify_chunk(
    client: AsyncTypeSafeClient,
    sem: asyncio.Semaphore,
    start_index: int,
    lines: list[str],
    model: str | None,
) -> list[tuple[int, float]]:
    state = {
        "log_lines": [
            {"index": i, "text": line} for i, line in enumerate(lines)
        ]
    }
    questions = build_questions(lines)

    async with sem:
        try:
            response = await client.system_one(state=state, questions=questions, model=model)
        except Exception as exc:
            print(f"warning: chunk starting at line {start_index} failed: {exc}", file=sys.stderr)
            return []

    results = []
    for i in range(len(lines)):
        answer = response.nouls.get(f"line_{i}")
        if answer is not None:
            results.append((start_index + i, answer.noul))
    return results


def chunked(items: list[str], size: int):
    for i in range(0, len(items), size):
        yield i, items[i : i + size]


async def run(args: argparse.Namespace) -> None:
    with open(args.log_file, encoding="utf-8", errors="replace") as f:
        lines = [line.rstrip("\n") for line in f]

    sem = asyncio.Semaphore(args.concurrency)
    flagged_scores: dict[int, float] = {}

    async with AsyncTypeSafeClient() as client:
        tasks = [
            classify_chunk(client, sem, start, chunk, args.model)
            for start, chunk in chunked(lines, args.chunk_size)
        ]
        total = len(tasks)
        done = 0
        for coro in asyncio.as_completed(tasks):
            for index, score in await coro:
                if score >= args.threshold:
                    flagged_scores[index] = score
            done += 1
            if done % 20 == 0 or done == total:
                print(f"processed {done}/{total} chunks", file=sys.stderr)

    with open(args.output, "w", encoding="utf-8") as out:
        for index in sorted(flagged_scores):
            out.write(lines[index] + "\n")

    print(f"flagged {len(flagged_scores)}/{len(lines)} lines -> {args.output}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_file", help="Path to the log file to scan")
    parser.add_argument("-o", "--output", default="flagged.txt", help="Output file for flagged lines")
    parser.add_argument("--chunk-size", type=int, default=40, help="Log lines batched per API call")
    parser.add_argument("--concurrency", type=int, default=16, help="Max concurrent API calls")
    parser.add_argument("--threshold", type=float, default=0.5, help="Noul score above which a line is flagged")
    parser.add_argument("--model", default=None, help="Override the Jev model (defaults to the SDK's default)")
    args = parser.parse_args()

    asyncio.run(run(args))


if __name__ == "__main__":
    main()
