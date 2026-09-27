"""compare.py decides the published scores, so its two rules are pinned here.

The panel takes the majority of the judges' verdicts, and a check's lead counts
only when a 95% Newcombe interval on the two pass rates lies above zero.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals/lib"))
import compare  # noqa: E402

BASELINE = ROOT / "evals/runs/2026-09-26T11-43-49Z"


class NewcombeLead(unittest.TestCase):
    def test_ten_against_six_counts_and_seven_does_not(self):
        self.assertTrue(compare.newcombe_lead(10, 10, 6, 10))
        self.assertFalse(compare.newcombe_lead(10, 10, 7, 10))

    def test_a_tie_is_never_a_lead(self):
        self.assertFalse(compare.newcombe_lead(10, 10, 10, 10))
        self.assertFalse(compare.newcombe_lead(0, 10, 0, 10))


class Panel(unittest.TestCase):
    def write(self, lines_by_judge: dict[str, list[dict]]) -> Path:
        path = Path(tempfile.mkdtemp())
        (path / "rejudge").mkdir()
        for judge, lines in lines_by_judge.items():
            (path / "rejudge" / f"{judge}.jsonl").write_text("\n".join(json.dumps(x) for x in lines))
        return path

    def test_two_judges_outvote_the_run(self):
        line = {"case": "c", "arm": "with", "run": 1, "check": "k", "opus_passed": True}
        path = self.write({"a": [{**line, "passed": False}], "b": [{**line, "passed": False}]})
        judges, verdicts = compare.panel(path, {"suite": {"judgeModel": "opus"}})
        self.assertEqual(["opus", "a", "b"], judges)
        self.assertEqual({("c", "with", 1, "k"): False}, verdicts)

    def test_a_missing_verdict_stops_the_comparison(self):
        line = {"case": "c", "arm": "with", "run": 1, "check": "k", "opus_passed": True, "passed": True}
        path = self.write({"a": [line], "b": []})
        with self.assertRaises(SystemExit):
            compare.panel(path, {})

    def test_no_rejudge_keeps_the_run_as_scored(self):
        self.assertEqual(([], {}), compare.panel(Path(tempfile.mkdtemp()), {}))


@unittest.skipUnless(BASELINE.with_name(BASELINE.name + "-this").exists(), "baseline not kept")
class AsRun(unittest.TestCase):
    def test_recomputed_scores_match_the_harness(self):
        for arm in ("none", "this", "official"):
            result = json.loads((BASELINE.with_name(f"{BASELINE.name}-{arm}") / "aggregate-result.json").read_text())
            ours = compare.run_scores(compare.graded_runs(result, {}))
            for case in result["cases"]:
                theirs = [r["score"] for r in next(iter(case["arms"].values()))]
                for a, b in zip(ours[case["name"]], theirs):
                    self.assertAlmostEqual(a, b, places=9, msg=f"{arm} {case['name']}")


if __name__ == "__main__":
    unittest.main()
