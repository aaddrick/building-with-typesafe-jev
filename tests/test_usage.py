"""usage.py is the only kept record of the agent's tokens, so pin what it reads."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals/lib"))
import usage  # noqa: E402


class Usage(unittest.TestCase):
    def test_reads_the_last_result_event_and_marks_a_missing_trace(self):
        d = Path(tempfile.mkdtemp())
        trace = d / "trace.jsonl"
        trace.write_text("\n".join([
            "not json",
            json.dumps({"type": "result", "usage": {"output_tokens": 1}}),
            json.dumps({"type": "result", "total_cost_usd": 0.5, "modelUsage": {"claude-sonnet-5": {}},
                        "usage": {"input_tokens": 3, "cache_read_input_tokens": 100,
                                  "output_tokens": 40, "output_tokens_details": {"thinking_tokens": 10}}}),
        ]))
        (d / "aggregate-result.json").write_text(json.dumps({"cases": [{"name": "c", "arms": {"with": [
            {"tracePath": str(trace)}, {"tracePath": str(d / "gone.jsonl")}]}}]}))
        first, second = usage.usage(d)
        self.assertEqual(3, first["input_tokens"])
        self.assertEqual(100, first["cache_read_input_tokens"])
        self.assertEqual(0, first["cache_creation_input_tokens"])
        self.assertEqual(40, first["output_tokens"])
        self.assertEqual(10, first["thinking_tokens"])
        self.assertEqual(["claude-sonnet-5"], first["models"])
        self.assertTrue(second["missing"])


if __name__ == "__main__":
    unittest.main()
