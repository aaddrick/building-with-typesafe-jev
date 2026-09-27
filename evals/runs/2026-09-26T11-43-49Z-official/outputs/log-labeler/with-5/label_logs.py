#!/usr/bin/env python3
"""Flag application log lines that need an on-call engineer, using TypeSafe's Jev model.

Lines are bundled into batches and sent to the model as a single call per
batch (one Noul question per line, sharing the batch as state), and batches
are processed concurrently, so a 50k-line file only needs a few hundred API
round trips instead of one per line.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from typesafe_sdk import AsyncTypeSafeClient, Noul, NoulAnswer, TypeSafeError

DEFAULT_MODEL = "jev"
BATCH_SIZE = 40    # log lines bundled into a single API call
CONCURRENCY = 16   # API calls in flight at once
THRESHOLD = 0.5    # noul probability at/above which a line is flagged

NOUL_CRITERIA = {
    "true": (
        "The line reports something an on-call engineer must act on now: a crash, "
        "outage, data loss, security incident, failed health check, or "
        "repeated/escalating errors."
    ),
    "false": (
        "The line is routine: normal request/response logging, debug/info chatter, "
        "expected warnings, or anything that does not require a human to intervene."
    ),
}


def read_lines(path: Path) -> list[tuple[int, str]]:
    """Return (1-based line number, text) pairs for non-blank lines."""
    lines = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for i, raw in enumerate(f, start=1):
            text = raw.rstrip("\n")
            if text.strip():
                lines.append((i, text))
    return lines


def chunked(items, size):
    for start in range(0, len(items), size):
        yield items[start:start + size]


async def classify_chunk(client, chunk, model, threshold):
    """Ask one Noul question per line in the chunk, sharing a single API call."""
    numbers, texts = zip(*chunk)
    state = {"lines": list(texts)}
    questions = {
        f"line_{i}": Noul(
            instructions=f"Does `lines[{i}]` describe something that needs an on-call engineer?",
            criteria=NOUL_CRITERIA,
        )
        for i in range(len(texts))
    }
    response = await client.system_one(state=state, questions=questions, model=model)

    flagged = []
    for i, (line_no, text) in enumerate(zip(numbers, texts)):
        answer = response.answers[f"line_{i}"]
        assert isinstance(answer, NoulAnswer)
        if answer.noul >= threshold:
            flagged.append((line_no, text))
    return flagged


async def run(log_path, out_path, model, batch_size, concurrency, threshold):
    lines = read_lines(log_path)
    if not lines:
        out_path.write_text("")
        return

    chunks = list(chunked(lines, batch_size))
    semaphore = asyncio.Semaphore(concurrency)
    flagged_by_chunk = {}

    async def worker(chunk_index, chunk, client):
        async with semaphore:
            try:
                flagged_by_chunk[chunk_index] = await classify_chunk(client, chunk, model, threshold)
            except TypeSafeError as exc:
                print(f"warning: chunk {chunk_index} failed ({exc}); skipping {len(chunk)} lines", file=sys.stderr)
                flagged_by_chunk[chunk_index] = []

    async with AsyncTypeSafeClient() as client:
        await asyncio.gather(*(worker(idx, chunk, client) for idx, chunk in enumerate(chunks)))

    flagged_lines = []
    for idx in range(len(chunks)):
        flagged_lines.extend(flagged_by_chunk.get(idx, []))
    flagged_lines.sort(key=lambda pair: pair[0])

    with out_path.open("w", encoding="utf-8") as f:
        for _, text in flagged_lines:
            f.write(text + "\n")

    print(
        f"processed {len(lines)} lines in {len(chunks)} requests, flagged {len(flagged_lines)}",
        file=sys.stderr,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logfile", type=Path, help="path to the application log file")
    parser.add_argument("--out", type=Path, default=Path("flagged.txt"), help="output file for flagged lines")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="TypeSafe model to use")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="log lines per API call")
    parser.add_argument("--concurrency", type=int, default=CONCURRENCY, help="concurrent API calls in flight")
    parser.add_argument("--threshold", type=float, default=THRESHOLD, help="noul probability threshold for flagging")
    args = parser.parse_args()

    asyncio.run(run(args.logfile, args.out, args.model, args.batch_size, args.concurrency, args.threshold))


if __name__ == "__main__":
    main()
