#!/usr/bin/env python3
"""Flag log lines that need an on-call engineer, using typesafe.ai's Jev model.

Usage:
    python label_logs.py app.log [-o flagged.txt]

Requires TYPESAFE_API_KEY in the environment and `pip install typesafe-sdk`.
"""

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from typesafe_sdk import Noul, NoulCriteria, TypeSafeClient, TypeSafeAPIError

# --- tunables (rule: keep questions/thresholds/weights in one place) ---
MODEL = "jev-latest"          # pin to e.g. "jev-1.13.0" once thresholds below are tuned against it
BATCH_SIZE = 40               # log lines per request; keeps state+questions well under the 64k token limit
MAX_WORKERS = 8               # shared-key rate limit (1,200 req/min) starts 429-ing above this
NOUL_THRESHOLD = 0.6          # P(needs on-call) at or above this -> flag. Tune on real labeled data.

QUESTION_INSTRUCTIONS = (
    "Does `lines[{i}]` describe a problem serious enough that an on-call engineer "
    "should be paged right now (e.g. a crash, outage, data loss, security incident, "
    "or a failure that will keep getting worse without a human), rather than routine "
    "or informational activity?"
)
QUESTION_CRITERIA = NoulCriteria(
    true="Service-impacting failure, crash, security incident, or a condition that "
         "will worsen without human intervention",
    false="Routine or informational log line, or an error that is already handled/recovered",
)


def build_questions(batch_size: int) -> dict:
    return {
        f"l{i}": Noul(instructions=QUESTION_INSTRUCTIONS.format(i=i), criteria=QUESTION_CRITERIA)
        for i in range(batch_size)
    }


def label_batch(client: TypeSafeClient, batch: list[str]) -> list[bool]:
    """Returns one flag per line in `batch`. Falls back to flagging everything
    in the batch if Jev can't answer, so a service hiccup can't silently drop a page."""
    questions = build_questions(len(batch))
    state = {"lines": [line.rstrip("\n") for line in batch]}
    try:
        r = client.system_one(state=state, questions=questions, model=MODEL)
    except TypeSafeAPIError as e:
        print(f"warning: batch of {len(batch)} lines failed ({e}); flagging for manual review", file=sys.stderr)
        return [True] * len(batch)
    return [r.nouls[f"l{i}"].noul >= NOUL_THRESHOLD for i in range(len(batch))]


def chunk(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logfile", help="path to the log file, one entry per line")
    parser.add_argument("-o", "--output", default="flagged.txt", help="where to write flagged lines")
    args = parser.parse_args()

    with open(args.logfile, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    # blank lines can't need paging and cost a question slot for nothing
    indexed_lines = [(i, line) for i, line in enumerate(lines) if line.strip()]
    batches = list(chunk(indexed_lines, BATCH_SIZE))

    start = time.monotonic()
    flagged = [False] * len(lines)
    with TypeSafeClient() as client:
        def process(batch):
            texts = [line for _, line in batch]
            flags = label_batch(client, texts)
            return [(idx, flag) for (idx, _), flag in zip(batch, flags)]

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            for results in pool.map(process, batches):
                for idx, flag in results:
                    flagged[idx] = flag

    with open(args.output, "w", encoding="utf-8") as out:
        for line, is_flagged in zip(lines, flagged):
            if is_flagged:
                out.write(line if line.endswith("\n") else line + "\n")

    elapsed = time.monotonic() - start
    print(f"model={MODEL} lines={len(lines)} flagged={sum(flagged)} elapsed={elapsed:.1f}s -> {args.output}")


if __name__ == "__main__":
    main()
