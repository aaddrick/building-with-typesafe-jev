"""install_muse.sh rewrites the frontmatter, so pin the shape Muse loads.

Muse only loads a skill whose name uses underscores and whose name and
description are one-line quoted strings. Nothing else checks the installed copy.
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "install_muse.sh"
SKILL = ROOT / "skills" / "building-with-typesafe-jev"


def install(source: Path, dest: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "MUSE_SKILL_SOURCE": str(source), "MUSE_SKILLS_DIR": str(dest)}
    return subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True)


class InstallMuse(unittest.TestCase):
    def setUp(self):
        self.dest = Path(tempfile.mkdtemp()) / "skills"

    def test_installs_the_skill_with_muse_frontmatter(self):
        result = install(SKILL, self.dest)
        self.assertEqual(0, result.returncode, result.stderr)
        installed = (self.dest / SKILL.name / "SKILL.md").read_text(encoding="utf-8")
        head, body = installed.split("\n---\n", 1)
        lines = head.split("\n")
        self.assertEqual("---", lines[0])
        self.assertEqual('name: "building_with_typesafe_jev"', lines[1])
        self.assertTrue(lines[2].startswith('description: "Use when '), lines[2])
        self.assertTrue(lines[2].endswith('"'))
        self.assertEqual(3, len(lines))
        self.assertEqual((SKILL / "SKILL.md").read_text(encoding="utf-8").split("\n---\n", 1)[1], body)

    def test_copies_every_file_beside_the_skill(self):
        self.assertEqual(0, install(SKILL, self.dest).returncode)
        expected = {p.relative_to(SKILL) for p in SKILL.rglob("*")
                    if p.is_file() and "__pycache__" not in p.parts}
        found = {p.relative_to(self.dest / SKILL.name) for p in (self.dest / SKILL.name).rglob("*") if p.is_file()}
        self.assertEqual(expected, found)

    def test_escapes_quotes_and_drops_other_keys(self):
        source = Path(tempfile.mkdtemp()) / SKILL.name
        source.mkdir()
        (source / "SKILL.md").write_text(
            '---\nname: building-with-typesafe-jev\ndescription: Say "yes" to C:\\path\nlicense: MIT\n---\n\n# Body\n',
            encoding="utf-8")
        self.assertEqual(0, install(source, self.dest).returncode)
        installed = (self.dest / SKILL.name / "SKILL.md").read_text(encoding="utf-8")
        self.assertEqual('---\nname: "building_with_typesafe_jev"\n'
                         'description: "Say \\"yes\\" to C:\\\\path"\n---\n\n# Body\n', installed)

    def test_a_second_run_replaces_the_installed_copy(self):
        self.assertEqual(0, install(SKILL, self.dest).returncode)
        stale = self.dest / SKILL.name / "stale.md"
        stale.write_text("old", encoding="utf-8")
        self.assertEqual(0, install(SKILL, self.dest).returncode)
        self.assertFalse(stale.exists())

    def test_refuses_a_folder_without_frontmatter(self):
        source = Path(tempfile.mkdtemp()) / SKILL.name
        source.mkdir()
        (source / "SKILL.md").write_text("# No frontmatter\n", encoding="utf-8")
        result = install(source, self.dest)
        self.assertNotEqual(0, result.returncode)
        self.assertFalse((self.dest / SKILL.name).exists())


if __name__ == "__main__":
    unittest.main()
