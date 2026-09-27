#!/usr/bin/env python3
"""Flag log lines that need an on-call engineer, using TypeSafe's Jev model."""

import argparse
import asyncio
import sys

from typesafe_sdk import AsyncTypeSafeClient, Noul, RetryPolicy, TypeSafeAPIError

INSTRUCTIONS_TEMPLATE = (
    "Does the application log line at `lines[{i}]` describe a problem serious "
    "enough that an on-call engineer needs to be paged right now?"
)
CRITERIA = {
    "true": (
        "A crash, unhandled exception, service outage, data loss, security "
        "incident, resource exhaustion, or other critical failure needing "
        "immediate human intervention."
    ),
    "false": (
        "Routine informational or debug output, or an error that is already "
        "handled/recovered and does not need immediate attention."
    ),
}


def chunked(items, size):
    for start in range(0, len(items), size):
        yield items[start : start + size]


async def classify_batch(client, retry, batch, threshold):
    """Return the subset of (index, line) pairs in `batch` that should be flagged."""
    questions = {
        str(i): Noul(instructions=INSTRUCTIONS_TEMPLATE.format(i=i), criteria=CRITERIA)
        for i in range(len(batch))
    }
    state = {"lines": [line for _, line in batch]}

    try:
        response = await client.system_one(state=state, questions=questions, retry=retry)
    except TypeSafeAPIError as exc:
        first_idx = batch[0][0]
        last_idx = batch[-1][0]
        print(
            f"warning: batch for lines {first_idx}-{last_idx} failed ({exc}); "
            "flagging them for manual review",
            file=sys.stderr,
        )
        return list(batch)

    flagged = []
    for i, (idx, line) in enumerate(batch):
        if response.nouls[str(i)].noul >= threshold:
            flagged.append((idx, line))
    return flagged


async def run(args):
    with open(args.log_file, encoding="utf-8", errors="replace") as f:
        lines = [line.rstrip("\n") for line in f]

    non_blank = [(idx, line) for idx, line in enumerate(lines) if line.strip()]
    batches = list(chunked(non_blank, args.batch_size))

    retry = RetryPolicy(max_retries=5, backoff_max=10.0, timeout=60.0)
    semaphore = asyncio.Semaphore(args.concurrency)
    done = 0

    async def bounded_classify(batch):
        nonlocal done
        async with semaphore:
            result = await classify_batch(client, retry, batch, args.threshold)
        done += 1
        if done % 10 == 0 or done == len(batches):
            print(f"processed {done}/{len(batches)} batches", file=sys.stderr)
        return result

    async with AsyncTypeSafeClient(model=args.model) as client:
        results = await asyncio.gather(*(bounded_classify(batch) for batch in batches))

    flagged_indices = {idx for batch_result in results for idx, _ in batch_result}

    with open(args.output, "w", encoding="utf-8") as out:
        for idx, line in enumerate(lines):
            if idx in flagged_indices:
                out.write(line + "\n")

    print(f"flagged {len(flagged_indices)}/{len(lines)} lines -> {args.output}", file=sys.stderr)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_file", help="path to the log file, one entry per line")
    parser.add_argument("-o", "--output", default="flagged.txt", help="output file for flagged lines")
    parser.add_argument("--batch-size", type=int, default=100, help="log lines classified per API call")
    parser.add_argument("--concurrency", type=int, default=20, help="max in-flight API calls")
    parser.add_argument("--threshold", type=float, default=0.5, help="min probability to flag a line")
    parser.add_argument("--model", default=None, help="override the TypeSafe model (defaults to Jev)")
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
