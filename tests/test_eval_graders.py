"""The regex graders in evals/ decide scores with no judge to catch a mistake.

A pattern that misses a real case, such as a catch-all option named `general`
instead of `other`, scores the control arm wrong in silence. Each pattern here
gets strings it must match and strings it must not. The eval runs these
patterns as JavaScript regexes; the ones here use no syntax that differs
between JavaScript and Python.
"""

import re
import unittest
from pathlib import Path


EVALS = Path(__file__).resolve().parents[1] / "evals"
PATTERN = re.compile(r"^(?:pattern|input_match): '((?:[^']|'')*)'$", re.M)
FLAGS = re.compile(r"^flags: (\w+)$", re.M)

# (grader file, text, pattern should match)
CASES = [
    ("command-gate/graders/separate-flags.md", 'Noul(instructions="a")\nNoul(instructions="b")', True),
    ("command-gate/graders/separate-flags.md", '{"type": "noul"}, {"type": "noul"}', True),
    ("command-gate/graders/separate-flags.md", 'Noul(instructions="only one")', False),
    ("command-gate/graders/no-noul-confidence.md", 'r.nouls["danger"].confidence', True),
    ("command-gate/graders/no-noul-confidence.md", 'r.choices["verdict"].confidence', False),
    ("command-gate/graders/max-not-average.md", "risk = sum(ps) / len(ps)", True),
    ("command-gate/graders/max-not-average.md", "risk = max(ps)", False),
    ("log-labeler/graders/bounded-concurrency.md", "ThreadPoolExecutor(max_workers=32)", True),
    ("log-labeler/graders/bounded-concurrency.md", "MAX_WORKERS = 16", True),
    ("log-labeler/graders/bounded-concurrency.md", "asyncio.Semaphore(50)", True),
    ("log-labeler/graders/bounded-concurrency.md", "MAX_WORKERS = 8", False),
    ("log-labeler/graders/bounded-concurrency.md", "ThreadPoolExecutor(max_workers=8)", False),
    ("log-labeler/graders/no-hand-rolled-retry.md", "for attempt in range(3):", True),
    ("log-labeler/graders/no-hand-rolled-retry.md", "client = TypeSafeClient(retry=RetryPolicy(max_retries=5))", False),
    ("reply-grader/graders/no-numeric-levels.md", 'criteria=["1", "2", "3"]', True),
    ("reply-grader/graders/no-numeric-levels.md", "criteria=[str(i) for i in range(1, 11)]", True),
    ("reply-grader/graders/no-numeric-levels.md", 'criteria=["Rude or dismissive", "Neutral", "Warm"]', False),
    ("triage-ticket/graders/choice-has-catch-all.md", '"general": {', True),
    ("triage-ticket/graders/choice-has-catch-all.md", "Literal['billing', 'other']", True),
    ("triage-ticket/graders/choice-has-catch-all.md", '"billing": {', False),
    ("triage-ticket/graders/no-hand-rolled-retry.md", "except TypeSafeRateLimitError:\n    time.sleep(2)", True),
    ("triage-ticket/graders/no-hand-rolled-retry.md", "r = client.system_one(state, QUESTIONS)", False),
    # Catching the error to surface it is not a retry; the SDK's RetryPolicy retries.
    ("triage-ticket/graders/no-hand-rolled-retry.md", "except TypeSafeRateLimitError as e:\n    raise Busy(e.retry_after_ms) from e", False),
    ("triage-ticket/graders/no-hand-rolled-retry.md", "while attempt < max_retries:", True),
    ("triage-ticket/graders/no-hand-rolled-retry.md", "while retries_left > 0:", True),
    ("triage-ticket/graders/no-hand-rolled-retry.md", 'raise Busy(\n    "rate limit exceeded while triaging ticket", exc.retry_after_ms\n)', False),
    ("log-labeler/graders/no-hand-rolled-retry.md", "while attempt <= MAX_RETRIES:", True),
    ("log-labeler/graders/no-hand-rolled-retry.md", 'log.warning("rate limited while labeling; retry_after=%s", e.retry_after_ms)', False),
    ("triage-ticket/graders/probability-keys.md", "sev.probabilities.get(str(i), 0)", True),
    ("triage-ticket/graders/probability-keys.md", "sev.probabilities.get(top_level, 0.0)", False),
    ("triage-ticket/graders/records-model-version.md", 'MODEL = "jev-1.13.0"', True),
    ("triage-ticket/graders/records-model-version.md", 'log.info("model=%s", response.model)', True),
    ("triage-ticket/graders/records-model-version.md", 'result["model_version"] = data["model"]', True),
    ("triage-ticket/graders/records-model-version.md", 'model = body.get("model")', True),
    ("triage-ticket/graders/records-model-version.md", 'MODEL = "jev-latest"  # pin jev-1.13.0 in prod', False),
    ("triage-ticket/graders/records-model-version.md", 'self.model = "jev-latest"', False),
    ("triage-ticket/graders/records-model-version.md", 'payload["model"] = "jev-latest"', False),
    ("triage-ticket/graders/routes-on-confidence.md", "if dept.confidence < THRESHOLD:", True),
    ("triage-ticket/graders/routes-on-confidence.md", "confidence = dept.confidence", False),
    ("email-facts/graders/uses-date-objects.md", "d = date(y, m, day)", True),
    ("email-facts/graders/uses-date-objects.md", "ask Jev if the date passed", False),
]


def load(grader: str) -> re.Pattern:
    text = (EVALS / grader).read_text(encoding="utf-8")
    pattern = PATTERN.search(text).group(1).replace("''", "'")
    flags = re.I if (m := FLAGS.search(text)) and "i" in m.group(1) else 0
    return re.compile(pattern, flags)


class EvalGraderTest(unittest.TestCase):
    def test_every_regex_grader_is_covered(self):
        graders = {str(p.relative_to(EVALS)) for p in EVALS.glob("*/graders/*.md")
                   if "type: regex" in p.read_text(encoding="utf-8")}
        self.assertEqual(graders, {g for g, _, _ in CASES})

    def test_patterns_match_what_they_should(self):
        for grader, text, want in CASES:
            with self.subTest(grader=grader, text=text):
                self.assertEqual(want, bool(load(grader).search(text)))


if __name__ == "__main__":
    unittest.main()
