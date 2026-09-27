"""rejudge.py must ask other judges exactly what the harness asked Opus.

A different prompt, vote rule, or criterion would make a disagreement between
judges mean nothing. These pin each piece to what `claude plugin eval` 2.1.283
does, and check every llm grader parses. No test calls a judge.
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals/lib"))
import rejudge  # noqa: E402


class Prompt(unittest.TestCase):
    def test_matches_the_harness_template(self):
        self.assertEqual(
            rejudge.prompt("Row X.", "gate.py", "print(1)"),
            "You are grading the output of a coding agent against a criterion.\n\n"
            "Criterion:\nRow X.\n\n\nAgent output (file gate.py):\nprint(1)\n\n\n"
            "Respond with exactly one word: PASS or FAIL.",
        )

    def test_long_file_keeps_head_and_tail(self):
        text = "a" * rejudge.HEAD + "b" * 50 + "c" * rejudge.TAIL
        p = rejudge.prompt("c", "f.py", text)
        self.assertIn("[…50 chars elided…]", p)
        self.assertNotIn("b", p.split("Agent output")[1].split("Respond")[0])


class Vote(unittest.TestCase):
    def test_rule(self):
        self.assertTrue(rejudge.vote("PASS"))
        self.assertTrue(rejudge.vote("pass."))
        self.assertFalse(rejudge.vote("FAIL"))
        self.assertFalse(rejudge.vote("PASS, not FAIL"))
        self.assertFalse(rejudge.vote("PASSED"))
        self.assertFalse(rejudge.vote(""))
        self.assertFalse(rejudge.vote(None))


class Graders(unittest.TestCase):
    def test_every_llm_grader_parses(self):
        llm = []
        for f in sorted((ROOT / "evals").glob("*/graders/*.md")):
            meta, criteria = rejudge.split_grader(f.read_text())
            if meta["type"] == "llm":
                llm.append(f)
                self.assertTrue(meta["path"], f)
                self.assertIn("PASS", criteria, f)
                self.assertFalse(criteria.startswith("---"), f)
        self.assertEqual(len(llm), 13)


class Scores(unittest.TestCase):
    def test_opus_verdicts_reproduce_the_harness_score(self):
        runs = [p.parent for p in (ROOT / "evals/runs").glob("*/aggregate-result.json")]
        if not runs:
            self.skipTest("no kept runs")
        import json
        for run in runs:
            result = json.loads((run / "aggregate-result.json").read_text())
            want = {c["name"]: [r["score"] for rs in c["arms"].values() for r in rs] for c in result["cases"]}
            got = rejudge.scores(run, None)
            for case in want:
                for w, g in zip(want[case], got[case]):
                    self.assertAlmostEqual(w, g, places=6, msg=f"{run.name} {case}")


if __name__ == "__main__":
    unittest.main()
