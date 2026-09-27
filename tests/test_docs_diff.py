"""docs_diff.py gates what replaces the docs cache and what Claude is told changed, so pin both."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import docs_diff  # noqa: E402


def page(title, slug, body):
    return f"# {title}\nSource: https://docs.typesafe.ai/{slug}\n\n{body}\n\n"


OLD = page("Choice", "primitives/choice", "Up to 255 options.") + page("Models", "models", "Jev 1.13.")
NEW = (
    page("Choice", "primitives/choice", "Up to 512 options.")
    + page("Models", "models", "Jev 1.13.")
    + page("Streaming", "streaming", "New.")
)


class SplitPages(unittest.TestCase):
    def test_splits_on_title_and_source(self):
        pages = docs_diff.split_pages(OLD)
        self.assertEqual(list(pages), ["primitives/choice", "models"])
        self.assertEqual(pages["models"][0], "Models")
        self.assertIn("Jev 1.13.", pages["models"][1])

    def test_a_heading_without_a_source_line_stays_in_its_page(self):
        pages = docs_diff.split_pages(page("A", "a", "# Not a page\ntext"))
        self.assertEqual(list(pages), ["a"])


class Report(unittest.TestCase):
    def test_lists_added_and_changed_and_diffs_only_the_changed(self):
        out = docs_diff.report(OLD, NEW, "")
        self.assertIn("1 added, 0 removed, 1 changed", out)
        self.assertIn("- `streaming`: Streaming", out)
        self.assertIn("+Up to 512 options.", out)
        self.assertNotIn("+New.", out)

    def test_no_previous_copy_means_every_page_is_added(self):
        self.assertIn("0 pages before, 2 after: 2 added", docs_diff.report("", OLD, ""))


class Referenced(unittest.TestCase):
    def test_url_backticked_path_and_bare_cookbook_slug_count(self):
        self.assertTrue(docs_diff.referenced("models", "see https://docs.typesafe.ai/models.md"))
        self.assertTrue(docs_diff.referenced("primitives/advanced", "read `primitives/advanced`"))
        self.assertTrue(docs_diff.referenced("cookbooks/sde_cascade", "| Cascade | `sde_cascade` |"))

    def test_a_longer_path_does_not_count_for_its_parent(self):
        self.assertFalse(docs_diff.referenced("primitives", "docs.typesafe.ai/primitives/noul.md"))
        self.assertFalse(docs_diff.referenced("sdk/python", "`sdk/python/usage`"))


class Validate(unittest.TestCase):
    def test_refuses_a_body_with_no_pages(self):
        self.assertTrue(docs_diff.validate("<html>502 Bad Gateway</html>", OLD))

    def test_refuses_a_fetch_that_lost_over_half_the_pages(self):
        self.assertTrue(docs_diff.validate(page("A", "a", "x"), NEW))

    def test_accepts_the_docs(self):
        self.assertEqual(docs_diff.validate(NEW, OLD), [])
        self.assertEqual(docs_diff.validate(OLD, ""), [])


class LiveCache(unittest.TestCase):
    def test_the_committed_cache_parses(self):
        cache = ROOT / "upstream/typesafe-docs/llms-full.txt"
        self.assertGreater(len(docs_diff.split_pages(cache.read_text(encoding="utf-8"))), 50)


if __name__ == "__main__":
    unittest.main()
