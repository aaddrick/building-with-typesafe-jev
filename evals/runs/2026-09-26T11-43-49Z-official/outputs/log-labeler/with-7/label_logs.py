#!/usr/bin/env python3
"""Flag log lines that need an on-call engineer, using typesafe.ai's Jev model.

Requires TYPESAFE_API_KEY to be set in the environment, and the typesafe-sdk
package installed (`pip install typesafe-sdk`).

Log lines are judged independently, so many lines are packed into each
Jev call (as one Noul question per line over a shared `lines` array) and
many calls run concurrently, to get through a large file quickly without
paying a per-line round trip.
"""

import argparse
import asyncio
import sys

from typesafe_sdk import AsyncTypeSafeClient, Noul, RetryPolicy

MODEL = "jev-latest"
BATCH_SIZE = 20
CONCURRENCY = 10
THRESHOLD = 0.5

QUESTION_INSTRUCTIONS = (
    "Does the log line at `lines[{i}]` indicate a problem serious enough "
    "that an on-call engineer should be paged right now?"
)
QUESTION_CRITERIA = {
    "true": (
        "The line reports an active incident: a crash, fatal/unhandled "
        "error, service outage, data loss, security breach, or critical "
        "resource exhaustion requiring immediate human intervention."
    ),
    "false": (
        "The line is routine, informational, or debug output, or "
        "describes an already-handled/expected condition that does not "
        "need anyone paged."
    ),
}


def read_lines(path: str) -> list[str]:
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.readlines()


def make_batches(lines: list[str], batch_size: int) -> list[list[tuple[int, str]]]:
    non_blank = [(i, line) for i, line in enumerate(lines) if line.strip()]
    return [
        non_blank[start : start + batch_size]
        for start in range(0, len(non_blank), batch_size)
    ]


async def label_batch(
    client: AsyncTypeSafeClient,
    batch: list[tuple[int, str]],
    model: str,
) -> dict[int, float]:
    state = {"lines": [line.strip() for _, line in batch]}
    questions = {
        f"q{pos}": Noul(
            instructions=QUESTION_INSTRUCTIONS.format(i=pos),
            criteria=QUESTION_CRITERIA,
        )
        for pos in range(len(batch))
    }
    response = await client.system_one(state=state, questions=questions, model=model)
    return {
        line_index: response.answers[f"q{pos}"].noul
        for pos, (line_index, _) in enumerate(batch)
    }


async def label_file(
    lines: list[str],
    batch_size: int,
    concurrency: int,
    model: str,
) -> dict[int, float]:
    batches = make_batches(lines, batch_size)
    scores: dict[int, float] = {}
    semaphore = asyncio.Semaphore(concurrency)
    done = 0

    async def run(batch: list[tuple[int, str]]) -> None:
        nonlocal done
        async with semaphore:
            try:
                result = await label_batch(client, batch, model)
                scores.update(result)
            except Exception as exc:
                first, last = batch[0][0], batch[-1][0]
                print(
                    f"warning: batch for lines {first}-{last} failed "
                    f"after retries, leaving unflagged: {exc}",
                    file=sys.stderr,
                )
            finally:
                done += 1
                if done % 50 == 0 or done == len(batches):
                    print(f"labeled {done}/{len(batches)} batches", file=sys.stderr)

    async with AsyncTypeSafeClient(retry=RetryPolicy(max_retries=5, timeout=30.0)) as client:
        await asyncio.gather(*(run(batch) for batch in batches))

    return scores


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_file", help="path to the application log file")
    parser.add_argument(
        "-o", "--output", default="flagged.txt", help="path to write flagged lines to"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help="log lines judged per Jev call (default: %(default)s)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=CONCURRENCY,
        help="concurrent Jev calls in flight (default: %(default)s)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=THRESHOLD,
        help=(
            "minimum on-call probability to flag a line (default: %(default)s). "
            "Lower it if missed incidents are costlier than noisy pages; "
            "raise it if false pages are costlier."
        ),
    )
    parser.add_argument("--model", default=MODEL, help="Jev model to use")
    args = parser.parse_args()

    lines = read_lines(args.log_file)
    scores = asyncio.run(
        label_file(lines, args.batch_size, args.concurrency, args.model)
    )

    flagged = [
        line for i, line in enumerate(lines) if scores.get(i, 0.0) >= args.threshold
    ]
    with open(args.output, "w", encoding="utf-8") as f:
        f.writelines(flagged)

    print(f"flagged {len(flagged)}/{len(lines)} lines -> {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
