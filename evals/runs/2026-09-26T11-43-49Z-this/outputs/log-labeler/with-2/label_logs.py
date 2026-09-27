#!/usr/bin/env python3
"""Flag log lines that need an on-call engineer, using typesafe.ai's Jev model."""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from typesafe_sdk import Noul, TypeSafeClient, TypeSafeError

BATCH_SIZE = 20            # lines per Jev request; keeps state well under the 64k-token cap
MAX_WORKERS = 8            # shared-key rate limit ceiling (typesafe.ai rate-limits above ~8 workers)
ON_CALL_THRESHOLD = 0.70   # Noul band: >0.70 = yes (patterns.md); re-tune once you have labeled data

ON_CALL_INSTRUCTIONS = (
    "Does `lines[{i}]` describe something that needs an on-call engineer to "
    "respond right now -- e.g. a service outage, crash, unhandled exception, "
    "failed health check, data loss, security incident, or an SLA/error-budget "
    "breach? Answer no for routine INFO/DEBUG output, expected warnings, or "
    "errors that are already marked resolved/retried successfully."
)


def make_questions(batch_len: int) -> dict:
    return {
        f"l{i}": Noul(instructions=ON_CALL_INSTRUCTIONS.format(i=i))
        for i in range(batch_len)
    }


def label_batch(client: TypeSafeClient, batch: list[str]):
    """Returns (list[bool] flagged-per-line, model_id_or_None)."""
    if not batch:
        return [], None
    try:
        r = client.system_one(state={"lines": batch}, questions=make_questions(len(batch)))
        flags = [r.nouls[f"l{i}"].noul > ON_CALL_THRESHOLD for i in range(len(batch))]
        return flags, r.model
    except TypeSafeError as e:
        print(f"warning: batch of {len(batch)} lines failed ({e}); flagging for manual review",
              file=sys.stderr)
        return [True] * len(batch), None


def chunked(seq: list, size: int):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logfile")
    parser.add_argument("-o", "--output", default="flagged.txt")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    args = parser.parse_args()

    with open(args.logfile, encoding="utf-8", errors="replace") as f:
        lines = [line.rstrip("\n") for line in f]

    non_empty_idx = [i for i, line in enumerate(lines) if line.strip()]
    idx_batches = list(chunked(non_empty_idx, args.batch_size))

    flagged = [False] * len(lines)
    models_seen: set[str] = set()

    with TypeSafeClient() as client, ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(label_batch, client, [lines[i] for i in idx_batch]): idx_batch
            for idx_batch in idx_batches
        }
        for future in as_completed(futures):
            idx_batch = futures[future]
            results, model = future.result()
            if model:
                models_seen.add(model)
            for i, is_flagged in zip(idx_batch, results):
                flagged[i] = is_flagged

    with open(args.output, "w", encoding="utf-8") as out:
        for line, is_flagged in zip(lines, flagged):
            if is_flagged:
                out.write(line + "\n")

    print(f"{sum(flagged)} of {len(lines)} lines flagged -> {args.output}")
    if models_seen:
        print(f"answered by: {', '.join(sorted(models_seen))}")


if __name__ == "__main__":
    main()
