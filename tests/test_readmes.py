"""The translated READMEs mirror the English one. Nothing else checks them.

A translation drifts in silence: an install command changes, and the English
README is the only file anyone rereads. These assertions cover the drifts that
reach a reader as a wrong command or a renamed identifier.
They do not check the prose. A translator still owns that.
"""

import collections
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENGLISH = ROOT / "README.md"
TRANSLATIONS = sorted((ROOT / ".github" / "readme").glob("README.*.md"))
LANGUAGES = {"zh-CN", "ja", "ko", "vi", "pt-BR", "it"}

INLINE_CODE = re.compile(r"`([^`\n]+)`")
# A fence in one of these languages holds commands or settings. Every README
# must carry it character for character, whatever the surrounding prose.
VERBATIM_FENCES = frozenset({"bash", "json", "fish", "powershell", ""})


def fenced_lines(text: str) -> list[str]:
    lines, inside, language = [], False, ""
    for line in text.split("\n"):
        if line.startswith("```"):
            inside = not inside
            language = line[3:].strip() if inside else ""
            continue
        if inside and language in VERBATIM_FENCES and line.strip():
            lines.append(line.strip())
    return lines


def inline_code(text: str) -> collections.Counter:
    return collections.Counter(INLINE_CODE.findall(text))


class ReadmeTest(unittest.TestCase):
    def setUp(self):
        self.english = ENGLISH.read_text(encoding="utf-8")

    def test_every_language_has_a_translation(self):
        found = {p.name[len("README."):-len(".md")] for p in TRANSLATIONS}
        self.assertEqual(LANGUAGES, found)

    def test_every_translation_carries_the_same_commands(self):
        expected = fenced_lines(self.english)
        self.assertTrue(expected, "the English README lists no commands")
        for path in TRANSLATIONS:
            with self.subTest(readme=path.name):
                self.assertEqual(expected, fenced_lines(path.read_text(encoding="utf-8")))

    def test_every_readme_names_the_same_code(self):
        # Compare as a multiset: some languages reorder code spans inside a
        # sentence, and word order is the translator's business.
        expected = inline_code(self.english)
        for path in TRANSLATIONS:
            with self.subTest(readme=path.name):
                found = inline_code(path.read_text(encoding="utf-8"))
                self.assertEqual(expected, found,
                                 f"missing: {expected - found} / extra: {found - expected}")

    def test_every_readme_links_every_language(self):
        for path in [ENGLISH, *TRANSLATIONS]:
            with self.subTest(readme=path.name):
                text = path.read_text(encoding="utf-8")
                for lang in LANGUAGES:
                    if path.name != f"README.{lang}.md":
                        self.assertIn(f"README.{lang}.md", text)


if __name__ == "__main__":
    unittest.main()
