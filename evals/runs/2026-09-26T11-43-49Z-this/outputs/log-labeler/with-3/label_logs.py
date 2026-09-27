#!/usr/bin/env python3
"""Flag application log lines that need an on-call engineer, using typesafe.ai's Jev model."""

import argparse
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from typesafe_sdk import Noul, TypeSafeClient, TypeSafeError

# --- tunables -------------------------------------------------------------

MODEL = "jev-1.13.0"          # pin the version thresholds below were chosen for
BATCH_SIZE = 50               # log lines judged per request (state dominates tokens, not question count)
MAX_WORKERS = 8               # shared-key rate limit starts biting above ~8 concurrent workers
NOUL_THRESHOLD = 0.8          # P(needs on-call) above which a line is flagged

# Broad recall net: only lines that look even remotely like trouble are sent
# to Jev. On a typical app log this cuts the model-call volume by 90%+ before
# any judgment call is made, which is where the real time/cost goes on 50k lines.
CANDIDATE_PATTERN = re.compile(
    r"error|warn|exception|fail|panic|fatal|critical|timeout"
    r"|denied|refused|unreachable|crash|traceback|deadlock|oom"
    r"|\b5\d\d\b",
    re.IGNORECASE,
)


def question_text(index: int) -> str:
    return (
        f"Does `lines.{index}` describe a problem serious enough to page an "
        "on-call engineer right now (an outage, crash, data loss, security "
        "incident, or an unrecoverable/production-impacting error), as opposed "
        "to routine, informational, retried-and-recovered, or already-handled "
        "output?"
    )


def read_candidates(path):
    """Yield (line_number, text) for lines worth sending to Jev."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f):
            text = line.rstrip("\n")
            if text and CANDIDATE_PATTERN.search(text):
                yield lineno, text


def chunked(iterable, size):
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def label_batch(client, batch):
    """batch: list of (lineno, text). Returns (flagged [(lineno, text)], model)."""
    state = {"lines": {str(i): text for i, (_, text) in enumerate(batch)}}
    questions = {f"q{i}": Noul(instructions=question_text(i)) for i in range(len(batch))}
    r = client.system_one(state=state, questions=questions, model=MODEL)
    flagged = [
        (lineno, text)
        for i, (lineno, text) in enumerate(batch)
        if r.nouls[f"q{i}"].noul > NOUL_THRESHOLD
    ]
    return flagged, r.model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_file", help="path to the application log file")
    parser.add_argument("-o", "--output", default="flagged.txt", help="output path (default: flagged.txt)")
    args = parser.parse_args()

    candidates = list(read_candidates(args.log_file))
    if not candidates:
        open(args.output, "w").close()
        print("no candidate lines found; wrote empty output")
        return

    flagged_by_lineno = {}
    models_seen = set()

    with TypeSafeClient() as client:
        batches = list(chunked(candidates, BATCH_SIZE))
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(label_batch, client, batch): batch for batch in batches}
            for future in as_completed(futures):
                batch = futures[future]
                try:
                    flagged, model = future.result()
                except TypeSafeError as e:
                    first_line = batch[0][0] + 1
                    print(f"warning: batch starting at line {first_line} failed: {e}", file=sys.stderr)
                    continue
                models_seen.add(model)
                for lineno, text in flagged:
                    flagged_by_lineno[lineno] = text

    with open(args.output, "w", encoding="utf-8") as f:
        for lineno in sorted(flagged_by_lineno):
            f.write(flagged_by_lineno[lineno] + "\n")

    print(
        f"{len(candidates)} candidate lines judged, {len(flagged_by_lineno)} flagged "
        f"-> {args.output} (model: {', '.join(sorted(models_seen)) or 'none'})"
    )


if __name__ == "__main__":
    main()
