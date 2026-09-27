#!/usr/bin/env python3
"""Flag log lines that need on-call attention, using typesafe.ai's Jev model.

Usage:
    pip install typesafe-sdk
    export TYPESAFE_API_KEY=...
    python label_logs.py app.log -o flagged.txt
"""

import argparse
import asyncio
import sys

from typesafe_sdk import (
    AsyncTypeSafeClient,
    Noul,
    NoulCriteria,
    RetryPolicy,
    TypeSafeError,
)

QUESTION_INSTRUCTIONS = (
    'Does the log line labeled "line_{n}" in state.lines indicate a problem '
    "serious enough that an on-call engineer should be paged right now (e.g. "
    "a crash, outage, unhandled exception, data loss, or security incident)?"
)
TRUE_CRITERIA = (
    "A severe error, crash, outage, or security event needing immediate "
    "human attention"
)
FALSE_CRITERIA = "Routine, informational, or minor/warning-level output"


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_file", help="path to the log file (one entry per line)")
    parser.add_argument("-o", "--output", default="flagged.txt", help="output path for flagged lines (default: flagged.txt)")
    parser.add_argument("--model", default=None, help="Jev model to use (default: SDK default, jev-latest)")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.3,
        help=(
            "minimum Noul probability to flag a line (default: 0.3 -- biased "
            "toward not missing real incidents, per typesafe.ai's uncertainty-"
            "band guidance where 0.3-0.7 is 'uncertain')"
        ),
    )
    parser.add_argument("--concurrency", type=int, default=20, help="max in-flight API requests (default: 20)")
    parser.add_argument(
        "--requests-per-second",
        type=float,
        default=15.0,
        help="cap on request starts/sec, kept under Jev's 1,200 req/min limit (default: 15)",
    )
    parser.add_argument("--max-lines-per-batch", type=int, default=100, help="max log lines packed into one API request (default: 100)")
    parser.add_argument(
        "--max-chars-per-batch",
        type=int,
        default=20000,
        help="max total characters per batch, to stay within Jev's context window (default: 20000)",
    )
    return parser.parse_args()


def read_lines(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return [(i, line.rstrip("\r\n")) for i, line in enumerate(f, start=1) if line.strip()]


def chunk_lines(lines, max_lines, max_chars):
    batch = []
    chars = 0
    for entry in lines:
        text_len = len(entry[1])
        if batch and (len(batch) >= max_lines or chars + text_len > max_chars):
            yield batch
            batch, chars = [], 0
        batch.append(entry)
        chars += text_len
    if batch:
        yield batch


def build_request(batch):
    state = {"lines": {f"line_{n}": text for n, text in batch}}
    questions = {
        f"line_{n}": Noul(
            instructions=QUESTION_INSTRUCTIONS.format(n=n),
            criteria=NoulCriteria(true=TRUE_CRITERIA, false=FALSE_CRITERIA),
        )
        for n, _ in batch
    }
    return state, questions


class RateLimiter:
    """Paces request starts to at most `rate` per second, independent of concurrency."""

    def __init__(self, rate):
        self._interval = 1.0 / rate
        self._lock = asyncio.Lock()
        self._next_time = 0.0

    async def wait(self):
        async with self._lock:
            loop_time = asyncio.get_event_loop().time()
            self._next_time = max(self._next_time, loop_time)
            delay = self._next_time - loop_time
            self._next_time += self._interval
        if delay > 0:
            await asyncio.sleep(delay)


async def process_batch(client, sem, limiter, batch, threshold, model):
    state, questions = build_request(batch)
    async with sem:
        await limiter.wait()
        try:
            response = await client.system_one(state=state, questions=questions, model=model)
        except TypeSafeError as exc:
            print(
                f"warning: batch (lines {batch[0][0]}-{batch[-1][0]}) failed, skipping: {exc}",
                file=sys.stderr,
            )
            return []

    return [
        (n, text)
        for n, text in batch
        if (answer := response.answers.get(f"line_{n}")) is not None and answer.noul >= threshold
    ]


async def run(args):
    lines = read_lines(args.log_file)
    batches = list(chunk_lines(lines, args.max_lines_per_batch, args.max_chars_per_batch))

    sem = asyncio.Semaphore(args.concurrency)
    limiter = RateLimiter(args.requests_per_second)

    async with AsyncTypeSafeClient(retry=RetryPolicy(max_retries=5, timeout=60.0)) as client:
        results = await asyncio.gather(
            *(
                process_batch(client, sem, limiter, batch, args.threshold, args.model)
                for batch in batches
            )
        )

    flagged = {n: text for batch_result in results for n, text in batch_result}

    with open(args.output, "w", encoding="utf-8") as out:
        for n in sorted(flagged):
            out.write(flagged[n] + "\n")

    print(f"Flagged {len(flagged)} of {len(lines)} lines -> {args.output}", file=sys.stderr)


def main():
    asyncio.run(run(parse_args()))


if __name__ == "__main__":
    main()
