#!/usr/bin/env python3
"""Flag log lines that need an on-call engineer, using typesafe.ai's Jev model.

Usage: python3 label_logs.py [log_path] [out_path]
Requires: pip install typesafe-sdk, and TYPESAFE_API_KEY set in the environment.
"""

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from typesafe_sdk import Noul, NoulCriteria, TypeSafeClient

# Tunable constants: model, batch shape, and the paging threshold.
MODEL = "jev-1.13.0"
BATCH_SIZE = 50  # lines per request; keeps state well under the context limit
MAX_WORKERS = 8  # shared-key rate limit starts 429ing above this
THRESHOLD = 0.5  # noul > THRESHOLD -> flagged; flagged.txt is for human review, not auto-paging

NEEDS_ONCALL = NoulCriteria(
    true=(
        "An active outage, crash, service failure, data loss, security incident, "
        "or resource exhaustion that a human needs to act on right now."
    ),
    false=(
        "Normal operation, a successful completion, routine informational status, "
        "or a warning/error that resolves on its own without human action."
    ),
)


def chunk(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def build_questions(batch):
    return {
        f"line_{i}": Noul(
            instructions=(
                f"Does `lines[{i}]` report a problem serious enough that an "
                "on-call engineer needs to be paged right now?"
            ),
            criteria=NEEDS_ONCALL,
        )
        for i in range(len(batch))
    }


def label_batch(client, batch):
    response = client.system_one(
        state={"lines": batch},
        questions=build_questions(batch),
        model=MODEL,
    )
    return [response.nouls[f"line_{i}"].noul for i in range(len(batch))]


def main(log_path="log.txt", out_path="flagged.txt"):
    with open(log_path, encoding="utf-8", errors="replace") as f:
        lines = [line.rstrip("\n") for line in f if line.strip()]

    batches = list(chunk(lines, BATCH_SIZE))
    results = [None] * len(batches)

    with TypeSafeClient() as client:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {
                pool.submit(label_batch, client, batch): idx
                for idx, batch in enumerate(batches)
            }
            for future in as_completed(futures):
                results[futures[future]] = future.result()

    flagged = [
        line
        for batch, scores in zip(batches, results)
        for line, score in zip(batch, scores)
        if score > THRESHOLD
    ]

    with open(out_path, "w", encoding="utf-8") as f:
        for line in flagged:
            f.write(line + "\n")

    print(f"Flagged {len(flagged)} of {len(lines)} lines -> {out_path}")


if __name__ == "__main__":
    log_path = sys.argv[1] if len(sys.argv) > 1 else "log.txt"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "flagged.txt"
    main(log_path, out_path)
