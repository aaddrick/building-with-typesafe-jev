#!/usr/bin/env python3
"""Flag log lines that need an on-call engineer, using typesafe.ai's Jev model.

Usage:
    python3 label_logs.py app.log
    python3 label_logs.py app.log --output flagged.txt --threshold 0.7

Requires TYPESAFE_API_KEY to be set in the environment.
"""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from typesafe_sdk import Noul, NoulCriteria, RetryPolicy, TypeSafeAPIError, TypeSafeClient

# --- Tunables: review/adjust these against labeled examples from real incidents. ---

BATCH_SIZE = 25  # log lines per request; keeps request count (and rate-limit exposure) low
MAX_WORKERS = 8  # field-tested ceiling on a shared key before 429s get common
NOUL_THRESHOLD = 0.7  # flag when P(needs on-call) exceeds this
MODEL = "jev-1.13.0"

INSTRUCTIONS_TEMPLATE = (
    "Does `lines[{i}]` describe an event serious enough that an on-call engineer "
    "should be paged right now -- e.g. a service crash, an outage, data loss or "
    "corruption, a security incident, or a persistent failure affecting users or "
    "systems? Routine INFO/DEBUG output, expected or handled warnings, successful "
    "requests, and transient issues the system already recovered from do NOT need "
    "paging."
)
CRITERIA = NoulCriteria(
    true=(
        "Crash, outage, data loss, security incident, or an unrecovered "
        "persistent failure affecting users or systems"
    ),
    false=(
        "Routine info/debug output, an expected or already-handled warning, a "
        "successful operation, or a transient issue that already recovered"
    ),
)


def build_questions(n: int) -> dict:
    return {
        f"line_{i}": Noul(instructions=INSTRUCTIONS_TEMPLATE.format(i=i), criteria=CRITERIA)
        for i in range(n)
    }


# Fixed-size template reused for every full batch; sliced down for the final partial batch.
FULL_QUESTIONS = build_questions(BATCH_SIZE)


def chunked(items, size):
    for start in range(0, len(items), size):
        yield start, items[start : start + size]


def classify_batch(client: TypeSafeClient, batch_lines: list[str]) -> list[bool]:
    questions = FULL_QUESTIONS if len(batch_lines) == BATCH_SIZE else build_questions(len(batch_lines))
    response = client.system_one(
        state={"lines": batch_lines},
        questions=questions,
        model=MODEL,
    )
    return [response.nouls[f"line_{i}"].noul > NOUL_THRESHOLD for i in range(len(batch_lines))]


def main():
    global NOUL_THRESHOLD, BATCH_SIZE, FULL_QUESTIONS

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_file", help="path to the log file, one entry per line")
    parser.add_argument("--output", default="flagged.txt", help="where to write flagged lines")
    parser.add_argument("--threshold", type=float, default=NOUL_THRESHOLD)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    args = parser.parse_args()

    NOUL_THRESHOLD = args.threshold
    BATCH_SIZE = args.batch_size
    FULL_QUESTIONS = build_questions(BATCH_SIZE)

    with open(args.log_file, encoding="utf-8", errors="replace") as f:
        lines = [line.rstrip("\n") for line in f if line.strip()]

    if not lines:
        open(args.output, "w").close()
        print("No non-empty lines to process.")
        return

    flags = [None] * len(lines)
    failed_batches = 0
    total_input_tokens = 0
    batches = list(chunked(lines, BATCH_SIZE))
    done = 0

    retry = RetryPolicy(max_retries=5)
    with TypeSafeClient(retry=retry) as client:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            future_to_start = {
                pool.submit(classify_batch, client, batch_lines): start
                for start, batch_lines in batches
            }
            for future in as_completed(future_to_start):
                start = future_to_start[future]
                batch_len = len(lines[start : start + BATCH_SIZE])
                try:
                    results = future.result()
                    for offset, is_flagged in enumerate(results):
                        flags[start + offset] = is_flagged
                except TypeSafeAPIError as e:
                    # Fail safe: a batch we couldn't classify gets flagged for
                    # human review rather than silently dropped.
                    failed_batches += 1
                    print(f"warning: batch at line {start} failed ({e}); flagging for review", file=sys.stderr)
                    for offset in range(batch_len):
                        flags[start + offset] = True

                done += 1
                if done % 50 == 0 or done == len(batches):
                    print(f"processed {done}/{len(batches)} batches", file=sys.stderr)

    flagged_lines = [line for line, flag in zip(lines, flags) if flag]

    with open(args.output, "w", encoding="utf-8") as out:
        for line in flagged_lines:
            out.write(line + "\n")

    print(f"{len(flagged_lines)}/{len(lines)} lines flagged -> {args.output}")
    if failed_batches:
        print(f"{failed_batches} batch(es) could not be classified and were flagged for manual review", file=sys.stderr)


if __name__ == "__main__":
    main()
