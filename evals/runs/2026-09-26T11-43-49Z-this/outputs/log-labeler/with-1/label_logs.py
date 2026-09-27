#!/usr/bin/env python3
"""Flag application log lines that need an on-call engineer, using typesafe.ai's Jev model.

Usage:
    python3 label_logs.py app.log [-o flagged.txt]
"""

import argparse
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from typesafe_sdk import Noul, NoulCriteria, TypeSafeClient, TypeSafeError

MODEL = "jev-1.13.0"  # pin the version the threshold below was picked against
WORKERS = 8  # the practical ceiling on a shared key before hitting 429s
NOUL_THRESHOLD = 0.7  # tune against labeled examples from real incidents before relying on this

QUESTIONS = {
    "needs_oncall": Noul(
        instructions=(
            "Does this application log line describe a problem serious enough that an "
            "on-call engineer needs to be paged to investigate or fix it right now?"
        ),
        criteria=NoulCriteria(
            true=(
                "A crash, unhandled exception, failed critical dependency, data loss or "
                "corruption risk, security incident, or user-facing outage that needs "
                "immediate human attention."
            ),
            false=(
                "Routine informational, debug, or warning output; an error that is expected "
                "and self-recovers (e.g. a retried request that then succeeds); startup or "
                "shutdown noise; access logs with normal status codes."
            ),
        ),
    ),
}

# Deterministic safety net: these patterns unambiguously mean "page someone". A miss here
# can't be undone, so they're checked in code instead of left entirely to a judgment call.
# Jev only has to weigh in on lines this doesn't already catch.
CRITICAL_PATTERNS = re.compile(
    r"\b(FATAL|PANIC(?:KED)?|SEGV|SEGFAULT|OOMKilled|OutOfMemoryError|core dumped|"
    r"database is down|connection refused|disk full|out of disk space|unrecoverable|"
    r"data corrupt(?:ed|ion)?)\b",
    re.IGNORECASE,
)


def is_critical(line: str) -> bool:
    return bool(CRITICAL_PATTERNS.search(line))


def label_unique_line(client: TypeSafeClient, line: str) -> tuple[bool, int]:
    try:
        r = client.system_one(state={"log_line": line}, questions=QUESTIONS, model=MODEL)
    except TypeSafeError as exc:
        # Can't get a judgment after the SDK's built-in retries: fail toward caution
        # (flag it) rather than silently dropping a line that might need attention.
        print(f"warning: Jev call failed, flagging line as a precaution: {exc}", file=sys.stderr)
        return True, 0
    return r.nouls["needs_oncall"].noul >= NOUL_THRESHOLD, r.usage.input_tokens


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_file", help="path to the log file, one entry per line")
    parser.add_argument("-o", "--output", default="flagged.txt", help="output file for flagged lines")
    args = parser.parse_args()

    with open(args.log_file, encoding="utf-8", errors="replace") as f:
        lines = [line.rstrip("\n") for line in f]

    # Real logs repeat the same templated line thousands of times. Judge each distinct
    # line once and reuse the answer instead of paying for near-identical calls.
    verdicts: dict[str, bool] = {}
    to_judge = []
    for line in lines:
        if not line or line in verdicts:
            continue
        if is_critical(line):
            verdicts[line] = True
        else:
            verdicts[line] = None  # placeholder, resolved below
            to_judge.append(line)

    print(f"{len(lines)} lines, {len(to_judge)} unique lines need a Jev call", file=sys.stderr)

    start = time.monotonic()
    total_tokens = 0
    with TypeSafeClient() as client:
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            futures = {pool.submit(label_unique_line, client, line): line for line in to_judge}
            done = 0
            for future, line in ((f, futures[f]) for f in futures):
                flagged, tokens = future.result()
                verdicts[line] = flagged
                total_tokens += tokens
                done += 1
                if done % 1000 == 0:
                    print(f"  {done}/{len(to_judge)} judged", file=sys.stderr)

    elapsed = time.monotonic() - start
    cost = total_tokens / 1_000_000 * 0.042
    print(
        f"done in {elapsed:.1f}s, {total_tokens} input tokens (~${cost:.4f})",
        file=sys.stderr,
    )

    flagged_count = 0
    with open(args.output, "w", encoding="utf-8") as out:
        for line in lines:
            if line and verdicts.get(line):
                out.write(line + "\n")
                flagged_count += 1

    print(f"flagged {flagged_count}/{len(lines)} lines -> {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
