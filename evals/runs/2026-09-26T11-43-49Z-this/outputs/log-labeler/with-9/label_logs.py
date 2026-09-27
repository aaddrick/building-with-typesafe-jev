#!/usr/bin/env python3
"""Flag application log lines that need an on-call engineer, using TypeSafe Jev.

Usage:
    export TYPESAFE_API_KEY=...
    python3 label_logs.py app.log flagged.txt
"""
import argparse
from concurrent.futures import ThreadPoolExecutor

from typesafe_sdk import Noul, TypeSafeClient

# Constants module (rule: keep questions/thresholds/weights in one place to tune).
MODEL = "jev-latest"       # pin to a versioned ID (e.g. "jev-1.13.0") once thresholds are tuned
BATCH_SIZE = 25            # log lines per Jev request; keeps state+questions well under the 64k token cap
MAX_WORKERS = 8            # practical ceiling on a shared key before 429s
ONCALL_THRESHOLD = 0.5     # flag a line when P(needs on-call) is at or above this

QUESTION_TEMPLATE = (
    "Does `lines[{i}]` describe a problem serious enough that an on-call "
    "engineer should be paged right now (a crash, an outage, data loss, a "
    "security incident, or a failure that kept retrying without succeeding)? "
    "Answer false for routine info/debug output, expected warnings, and "
    "errors that were already handled or retried successfully."
)


def build_questions(batch: list[str]) -> dict[str, Noul]:
    return {str(i): Noul(instructions=QUESTION_TEMPLATE.format(i=i)) for i in range(len(batch))}


def label_batch(client: TypeSafeClient, batch: list[str]) -> tuple[list[str], int]:
    response = client.system_one(state={"lines": batch}, questions=build_questions(batch), model=MODEL)
    flagged = [line for i, line in enumerate(batch) if response.nouls[str(i)].noul >= ONCALL_THRESHOLD]
    return flagged, response.usage.input_tokens


def chunk(items: list[str], size: int):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_path", help="path to the input log file, one entry per line")
    parser.add_argument("out_path", nargs="?", default="flagged.txt", help="path to write flagged lines to")
    args = parser.parse_args()

    with open(args.log_path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    batches = list(chunk(lines, BATCH_SIZE))

    total_flagged = 0
    total_tokens = 0
    with TypeSafeClient() as client, open(args.out_path, "w", encoding="utf-8") as out:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            for flagged, tokens in pool.map(lambda b: label_batch(client, b), batches):
                for line in flagged:
                    out.write(line + "\n")
                total_flagged += len(flagged)
                total_tokens += tokens

    print(f"{len(lines)} lines -> {total_flagged} flagged, {total_tokens} input tokens (model {MODEL})")


if __name__ == "__main__":
    main()
