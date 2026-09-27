"""The docs pipeline, run step by step the way its three workflows run it.

scripts/docs_pipeline.py holds every decision the workflows make. These
tests drive it against tests/fake_gh.py (variables, artifacts, pull
requests) and a local bare git remote. The fetch, the artifact upload, and
the Claude call are the only workflow steps not run here; the tests stand in
for them by writing the docs, adding an artifact, and editing the skill.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "scripts" / "docs_pipeline.py"
WORKFLOWS = ROOT / ".github" / "workflows"
sys.path.insert(0, str(ROOT / "scripts"))
import docs_pipeline  # noqa: E402

BRANCH = "docs-sync/skill-coverage"
SKILL = "skills/building-with-typesafe-jev"
NOW = "2026-09-27T12:00:00Z"


def page(title, slug, body):
    return f"# {title}\nSource: https://docs.typesafe.ai/{slug}\n\n{body}\n\n"


DOCS_V1 = page("Choice", "primitives/choice", "Up to 255 options.") + page("Models", "models", "Jev 1.13.")
DOCS_V2 = page("Choice", "primitives/choice", "Up to 512 options.") + page("Models", "models", "Jev 1.13.")
DOCS_V3 = DOCS_V2 + page("Streaming", "streaming", "Stream answers as they land.")


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


class Pipeline(unittest.TestCase):
    """A fake GitHub, a clone of a repo with a skill, and helpers that run one workflow step each."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        gh = bin_dir / "gh"
        gh.write_text(f"#!/bin/sh\nexec {sys.executable} {ROOT / 'tests' / 'fake_gh.py'} \"$@\"\n")
        gh.chmod(0o755)
        self.state_file = self.tmp / "gh.json"
        self.save({"vars": {}, "artifacts": {}, "prs": {}, "calls": []})
        self.env = {
            **os.environ,
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            "FAKE_GH_STATE": str(self.state_file),
            "GITHUB_REPOSITORY": "o/r",
            "GH_TOKEN": "github-token",
            "VARS_TOKEN": "pat",
            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
        }
        self.env.pop("GITHUB_STEP_SUMMARY", None)
        self.next_run = 100
        self.origin = self.tmp / "origin.git"
        self.work = self.tmp / "work"
        self.git(self.tmp, "init", "-q", "--bare", "-b", "main", str(self.origin))
        self.git(self.tmp, "clone", "-q", str(self.origin), str(self.work))
        self.git(self.work, "checkout", "-q", "-b", "main")
        (self.work / SKILL).mkdir(parents=True)
        (self.work / SKILL / "SKILL.md").write_text("Choice takes up to 255 options.\n")
        (self.work / ".gitignore").write_text(".docs-cache/\n")
        self.git(self.work, "add", "-A")
        self.git(self.work, "commit", "-q", "-m", "init")
        self.git(self.work, "push", "-q", "origin", "main")

    # Fake GitHub state

    def load(self):
        return json.loads(self.state_file.read_text())

    def save(self, state):
        self.state_file.write_text(json.dumps(state))

    def var(self, name):
        return self.load()["vars"].get(name, "")

    def ref(self, name):
        return json.loads(self.var(name)) if self.var(name) else None

    def calls(self, *prefix):
        return [c for c in self.load()["calls"] if c[: len(prefix)] == list(prefix)]

    def add_artifact(self, text, expires_at="2026-12-26T00:00:00Z", expired=False):
        state = self.load()
        artifact_id = str(1000 + len(state["artifacts"]))
        state["artifacts"][artifact_id] = {"content": text, "expires_at": expires_at, "expired": expired}
        self.save(state)
        return int(artifact_id)

    # Running steps

    def git(self, cwd, *args):
        subprocess.run(["git", *args], cwd=cwd, check=True, env=getattr(self, "env", os.environ), capture_output=True)

    def run_step(self, *args, cwd=None, env=None, ok=True):
        out_file = self.tmp / "output.txt"
        out_file.write_text("")
        result = subprocess.run(
            [sys.executable, str(PIPELINE), *args], cwd=cwd or self.work, capture_output=True, text=True,
            env={**self.env, "GITHUB_OUTPUT": str(out_file), **(env or {})},
        )
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        outputs = dict(re.findall(r"^(\w+)<<__OUTPUT__\n(.*?)\n__OUTPUT__$", out_file.read_text(), re.M | re.S))
        return outputs, result.stdout

    def docs_cache(self, docs, now=NOW):
        """One docs-cache run: compare, upload when told to, record. Returns record-latest's outputs."""
        self.next_run += 1
        fetched = self.tmp / "fetched.txt"
        fetched.write_text(docs)
        compared, _ = self.run_step("compare", "--fetched", str(fetched), "--latest", self.var("DOCS_LATEST"), "--now", now)
        artifact_id = self.add_artifact(docs) if compared["upload"] == "true" else None
        recorded, _ = self.run_step(
            "record-latest", "--latest", self.var("DOCS_LATEST"), "--reviewed", self.var("DOCS_SKILL_REVIEWED"),
            "--uploaded", compared["upload"], "--run-id", str(self.next_run),
            "--artifact-id", str(artifact_id or ""), "--sha256", compared["sha256"], "--pages", compared["pages"],
        )
        return {**compared, **recorded}

    def skill_coverage(self, edit=None, force="false"):
        """One skill-coverage run, with `edit` standing in for Claude. Returns plan's and publish's outputs."""
        latest = self.var("DOCS_LATEST")
        plan, _ = self.run_step("plan", "--latest", latest, "--reviewed", self.var("DOCS_SKILL_REVIEWED"),
                                "--branch", BRANCH, "--force", force)
        if plan["run"] != "true":
            return plan
        if plan["pr"]:
            self.run_step("use-branch", "--branch", BRANCH, "--base-branch", "main")
        self.run_step("prepare", "--latest", latest, "--base", plan["base"], "--docs", ".docs-cache/llms-full.txt",
                      "--report", str(self.tmp / "report.md"), "--skill", SKILL)
        if edit:
            path = self.work / SKILL / "SKILL.md"
            path.write_text(path.read_text() + edit + "\n")
        (self.tmp / "summary.md").write_text("### Skill changes\n\n- something\n")
        published, _ = self.run_step(
            "publish", "--latest", latest, "--pr", plan["pr"], "--branch", BRANCH, "--base-branch", "main",
            "--skill", SKILL, "--summary", str(self.tmp / "summary.md"), "--report", str(self.tmp / "report.md"),
            "--run-url", "https://example.test/run", "--now", NOW,
        )
        self.git(self.work, "checkout", "-q", "main")
        return {**plan, **published}

    def merge(self, number):
        """Merge a pull request the way GitHub would, then run skill-reviewed."""
        state = self.load()
        pr = state["prs"][str(number)]
        pr["state"] = "merged"
        self.save(state)
        self.git(self.work, "fetch", "-q", "origin", pr["head"])
        self.git(self.work, "merge", "-q", "--no-edit", f"origin/{pr['head']}")
        self.git(self.work, "push", "-q", "origin", "main")
        return self.run_step("record-merged", "--reviewed", self.var("DOCS_SKILL_REVIEWED"), env={"PR_BODY": pr["body"]})

    def remote_file(self, ref, path):
        return subprocess.run(["git", "show", f"{ref}:{path}"], cwd=self.work, capture_output=True, text=True).stdout


class DocsCache(Pipeline):
    def test_first_run_caches_the_docs_and_takes_the_skill_as_reviewed(self):
        out = self.docs_cache(DOCS_V1)
        self.assertEqual((out["changed"], out["upload"], out["stale"]), ("true", "true", "false"))
        latest = self.ref("DOCS_LATEST")
        self.assertEqual(latest["sha256"], sha(DOCS_V1))
        self.assertEqual(latest["pages"], 2)
        self.assertEqual(self.ref("DOCS_SKILL_REVIEWED"), latest)

    def test_unchanged_docs_upload_nothing_and_set_no_variable(self):
        self.docs_cache(DOCS_V1)
        before = len(self.calls("variable", "set"))
        out = self.docs_cache(DOCS_V1)
        self.assertEqual((out["changed"], out["upload"], out["stale"]), ("false", "false", "false"))
        self.assertEqual(len(self.calls("variable", "set")), before)
        self.assertEqual(len(self.load()["artifacts"]), 1)

    def test_a_change_moves_latest_but_not_reviewed_and_marks_stale(self):
        self.docs_cache(DOCS_V1)
        out = self.docs_cache(DOCS_V2)
        self.assertEqual((out["changed"], out["stale"]), ("true", "true"))
        self.assertEqual(self.ref("DOCS_LATEST")["sha256"], sha(DOCS_V2))
        self.assertEqual(self.ref("DOCS_SKILL_REVIEWED")["sha256"], sha(DOCS_V1))

    def test_the_step_summary_shows_what_changed(self):
        self.docs_cache(DOCS_V1)
        summary = self.tmp / "summary.txt"
        self.env["GITHUB_STEP_SUMMARY"] = str(summary)
        self.docs_cache(DOCS_V3)
        text = summary.read_text()
        self.assertIn("1 added, 0 removed, 1 changed", text)
        self.assertNotIn("## Diffs", text)

    def test_an_artifact_near_expiry_is_renewed_and_reviewed_follows_it(self):
        self.docs_cache(DOCS_V1)
        old = self.ref("DOCS_LATEST")
        out = self.docs_cache(DOCS_V1, now="2026-12-20T00:00:00Z")
        self.assertEqual((out["changed"], out["upload"], out["stale"]), ("false", "true", "false"))
        self.assertNotEqual(self.ref("DOCS_LATEST")["artifact_id"], old["artifact_id"])
        self.assertEqual(self.ref("DOCS_SKILL_REVIEWED"), self.ref("DOCS_LATEST"))

    def test_renewal_leaves_an_older_reviewed_copy_alone(self):
        self.docs_cache(DOCS_V1)
        self.docs_cache(DOCS_V2)
        reviewed = self.ref("DOCS_SKILL_REVIEWED")
        out = self.docs_cache(DOCS_V2, now="2026-12-20T00:00:00Z")
        self.assertEqual((out["upload"], out["stale"]), ("true", "true"))
        self.assertEqual(self.ref("DOCS_SKILL_REVIEWED"), reviewed)

    def test_an_expired_or_missing_artifact_is_renewed(self):
        self.docs_cache(DOCS_V1)
        state = self.load()
        state["artifacts"].clear()
        self.save(state)
        self.assertEqual(self.docs_cache(DOCS_V1)["upload"], "true")

    def test_refuses_an_error_page_and_a_truncated_fetch(self):
        self.docs_cache(DOCS_V1 + page("C", "c", "x") + page("D", "d", "y"))
        fetched = self.tmp / "bad.txt"
        for bad in ("<html>502 Bad Gateway</html>", page("A", "a", "cut off")):
            fetched.write_text(bad)
            _, out = self.run_step("compare", "--fetched", str(fetched), "--latest", self.var("DOCS_LATEST"), ok=False)
            self.assertIn("::error::the fetched docs were refused", out)

    def test_recording_an_upload_without_gh_pat_fails_loudly(self):
        fetched = self.tmp / "f.txt"
        fetched.write_text(DOCS_V1)
        _, out = self.run_step("record-latest", "--uploaded", "true", "--run-id", "1", "--artifact-id", "2",
                               "--sha256", sha(DOCS_V1), "--pages", "2", env={"VARS_TOKEN": ""}, ok=False)
        self.assertIn("GH_PAT secret is not set", out)


class SkillCoverage(Pipeline):
    def test_nothing_to_do_when_the_skill_is_reviewed_against_the_latest_copy(self):
        self.docs_cache(DOCS_V1)
        self.assertEqual(self.skill_coverage(edit="x")["run"], "false")
        self.assertEqual(self.calls("pr", "create"), [])

    def test_force_runs_anyway(self):
        self.docs_cache(DOCS_V1)
        self.assertEqual(self.skill_coverage(force="true")["outcome"], "recorded")

    def test_a_change_with_skill_edits_opens_a_pull_request_that_covers_the_latest_copy(self):
        self.docs_cache(DOCS_V1)
        self.docs_cache(DOCS_V2)
        out = self.skill_coverage(edit="Choice takes up to 512 options.")
        self.assertEqual(out["outcome"], "opened")
        self.assertEqual(out["base"], self.var("DOCS_SKILL_REVIEWED"))
        pr = self.load()["prs"]["1"]
        self.assertEqual((pr["head"], pr["base"]), (BRANCH, "main"))
        self.assertEqual(docs_pipeline.find_marker(pr["body"]), self.ref("DOCS_LATEST"))
        self.assertIn("### Skill changes", pr["body"])
        self.assertIn("`primitives/choice`", pr["body"])
        self.assertIn("512 options", self.remote_file(f"origin/{BRANCH}", f"{SKILL}/SKILL.md"))
        self.assertEqual(self.remote_file(f"origin/{BRANCH}", ".docs-cache/llms-full.txt"), "")
        # The review is not recorded until the pull request merges.
        self.assertEqual(self.ref("DOCS_SKILL_REVIEWED")["sha256"], sha(DOCS_V1))

    def test_claude_reads_the_latest_copy_and_the_report_diffs_from_the_reviewed_one(self):
        self.docs_cache(DOCS_V1)
        self.docs_cache(DOCS_V2)
        self.skill_coverage(edit="x")
        self.assertEqual((self.work / ".docs-cache/llms-full.txt").read_text(), DOCS_V2)
        report = (self.tmp / "report.md").read_text()
        self.assertIn("+Up to 512 options.", report)
        self.assertIn("-Up to 255 options.", report)

    def test_an_open_pull_request_that_covers_the_latest_copy_is_not_reviewed_again(self):
        self.docs_cache(DOCS_V1)
        self.docs_cache(DOCS_V2)
        self.skill_coverage(edit="x")
        self.assertEqual(self.docs_cache(DOCS_V2)["stale"], "true")
        out = self.skill_coverage(edit="y")
        self.assertEqual((out["run"], out["pr"]), ("false", "1"))

    def test_a_newer_change_is_reviewed_on_top_of_the_open_pull_request(self):
        self.docs_cache(DOCS_V1)
        self.docs_cache(DOCS_V2)
        self.skill_coverage(edit="first edit")
        v2 = self.ref("DOCS_LATEST")
        self.docs_cache(DOCS_V3)
        out = self.skill_coverage(edit="second edit")
        self.assertEqual((out["outcome"], out["pr"]), ("updated", "1"))
        self.assertEqual(json.loads(out["base"]), v2)
        report = (self.tmp / "report.md").read_text()
        self.assertIn("1 added, 0 removed, 0 changed", report)
        skill = self.remote_file(f"origin/{BRANCH}", f"{SKILL}/SKILL.md")
        self.assertIn("first edit", skill)
        self.assertIn("second edit", skill)
        pr = self.load()["prs"]["1"]
        self.assertEqual(docs_pipeline.find_marker(pr["body"]), self.ref("DOCS_LATEST"))
        self.assertEqual(pr["body"].count("docs-review"), 1)
        self.assertIn("Pushed more edits.", pr["comments"][0])
        self.assertEqual(len(self.calls("pr", "create")), 1)

    def test_a_newer_change_needing_no_edits_still_moves_the_open_pull_requests_marker(self):
        self.docs_cache(DOCS_V1)
        self.docs_cache(DOCS_V2)
        self.skill_coverage(edit="x")
        head = self.remote_file(f"origin/{BRANCH}", f"{SKILL}/SKILL.md")
        self.docs_cache(DOCS_V3)
        self.assertEqual(self.skill_coverage()["outcome"], "updated")
        self.assertEqual(self.remote_file(f"origin/{BRANCH}", f"{SKILL}/SKILL.md"), head)
        self.assertEqual(docs_pipeline.find_marker(self.load()["prs"]["1"]["body"]), self.ref("DOCS_LATEST"))
        self.assertIn("No further edits needed.", self.load()["prs"]["1"]["comments"][0])

    def test_no_edits_and_no_pull_request_records_the_review_directly(self):
        self.docs_cache(DOCS_V1)
        self.docs_cache(DOCS_V2)
        self.assertEqual(self.skill_coverage()["outcome"], "recorded")
        self.assertEqual(self.ref("DOCS_SKILL_REVIEWED"), self.ref("DOCS_LATEST"))
        self.assertEqual(self.calls("pr", "create"), [])
        self.assertEqual(self.docs_cache(DOCS_V2)["stale"], "false")

    def test_an_expired_reviewed_copy_means_a_full_review(self):
        self.docs_cache(DOCS_V1)
        self.docs_cache(DOCS_V2)
        state = self.load()
        state["artifacts"][str(self.ref("DOCS_SKILL_REVIEWED")["artifact_id"])]["expired"] = True
        self.save(state)
        self.skill_coverage(edit="x")
        self.assertIn("0 pages before, 2 after: 2 added", (self.tmp / "report.md").read_text())

    def test_an_expired_latest_copy_fails_the_run(self):
        self.docs_cache(DOCS_V1)
        self.docs_cache(DOCS_V2)
        state = self.load()
        state["artifacts"][str(self.ref("DOCS_LATEST")["artifact_id"])]["expired"] = True
        self.save(state)
        _, out = self.run_step("prepare", "--latest", self.var("DOCS_LATEST"), "--docs", ".docs-cache/x.txt",
                               "--report", str(self.tmp / "r.md"), "--skill", SKILL, ok=False)
        self.assertIn("latest docs artifact is gone", out)

    def test_an_artifact_that_does_not_match_its_hash_is_not_used(self):
        self.docs_cache(DOCS_V1)
        state = self.load()
        state["artifacts"][str(self.ref("DOCS_LATEST")["artifact_id"])]["content"] = DOCS_V2
        self.save(state)
        _, out = self.run_step("prepare", "--latest", self.var("DOCS_LATEST"), "--docs", ".docs-cache/x.txt",
                               "--report", str(self.tmp / "r.md"), "--skill", SKILL, ok=False)
        self.assertIn("does not match its sha256", out)

    def test_plan_fails_before_the_first_docs_cache_run(self):
        _, out = self.run_step("plan", "--branch", BRANCH, ok=False)
        self.assertIn("DOCS_LATEST is not set", out)


class SkillReviewed(Pipeline):
    def open_and_merge(self):
        self.docs_cache(DOCS_V1)
        self.docs_cache(DOCS_V2)
        self.skill_coverage(edit="x")
        return self.merge(1)

    def test_merging_records_the_copy_the_pull_request_covers(self):
        self.open_and_merge()
        self.assertEqual(self.ref("DOCS_SKILL_REVIEWED"), self.ref("DOCS_LATEST"))
        self.assertEqual(self.docs_cache(DOCS_V2)["stale"], "false")

    def test_the_next_change_after_a_merge_opens_a_fresh_pull_request_from_the_merged_copy(self):
        self.open_and_merge()
        v2 = self.ref("DOCS_LATEST")
        self.docs_cache(DOCS_V3)
        out = self.skill_coverage(edit="z")
        self.assertEqual((out["outcome"], json.loads(out["base"])), ("opened", v2))
        self.assertEqual(len(self.calls("pr", "create")), 2)

    def test_never_moves_backward(self):
        self.docs_cache(DOCS_V1)
        old = self.ref("DOCS_LATEST")
        newer = {**old, "run_id": old["run_id"] + 5}
        state = self.load()
        state["vars"]["DOCS_SKILL_REVIEWED"] = json.dumps(newer)
        self.save(state)
        _, out = self.run_step("record-merged", "--reviewed", json.dumps(newer),
                               env={"PR_BODY": docs_pipeline.marker(old)})
        self.assertIn("already names a newer copy", out)
        self.assertEqual(self.ref("DOCS_SKILL_REVIEWED"), newer)

    def test_rejects_a_missing_or_malformed_marker(self):
        bodies = [
            "no marker",
            '<!-- docs-review: {"run_id": 1} -->',
            '<!-- docs-review: {"run_id":1,"artifact_id":2,"sha256":"$(curl evil)","pages":3} -->',
        ]
        for body in bodies:
            _, out = self.run_step("record-merged", env={"PR_BODY": body}, ok=False)
            self.assertIn("No valid docs-review marker", out)
        self.assertEqual(self.calls("variable", "set"), [])


class Refs(unittest.TestCase):
    GOOD = {"run_id": 1, "artifact_id": 2, "sha256": "a" * 64, "pages": 3}

    def test_round_trips_and_drops_extra_keys(self):
        ref = docs_pipeline.parse_ref(json.dumps({**self.GOOD, "extra": "x"}))
        self.assertEqual(ref, self.GOOD)
        self.assertEqual(docs_pipeline.find_marker("text\n" + docs_pipeline.marker(ref)), ref)

    def test_rejects_wrong_types(self):
        for bad in ("", "null", "[]", "{", json.dumps({**self.GOOD, "run_id": "1"}),
                    json.dumps({**self.GOOD, "pages": True}), json.dumps({**self.GOOD, "sha256": "A" * 64})):
            self.assertIsNone(docs_pipeline.parse_ref(bad), bad)

    def test_the_last_marker_wins(self):
        older = {**self.GOOD, "run_id": 0}
        body = docs_pipeline.marker(older) + "\n" + docs_pipeline.marker(self.GOOD)
        self.assertEqual(docs_pipeline.find_marker(body), self.GOOD)


class Workflows(unittest.TestCase):
    """The workflows stay wired to the pipeline and to the failure alert."""

    def text(self, name):
        return (WORKFLOWS / name).read_text(encoding="utf-8")

    def test_every_pipeline_command_a_workflow_calls_exists(self):
        commands = set()
        for name in ("docs-cache.yml", "skill-coverage.yml", "skill-reviewed.yml"):
            commands |= set(re.findall(r"docs_pipeline\.py ([\w-]+)", self.text(name)))
        known = {"compare", "record-latest", "plan", "use-branch", "prepare", "publish", "record-merged"}
        self.assertTrue(commands, "no workflow calls docs_pipeline.py")
        self.assertLessEqual(commands, known)
        self.assertEqual(commands, known, "a pipeline command is never called")

    def test_each_workflow_emails_on_failure(self):
        for name in ("docs-cache.yml", "skill-coverage.yml", "skill-reviewed.yml"):
            text = self.text(name)
            self.assertRegex(text, r"(?s)\n  alert:\n.*?if: .*failure\(\).*?uses: \./\.github/workflows/failure-alert\.yml", name)

    def test_docs_cache_alerts_on_either_job(self):
        self.assertRegex(self.text("docs-cache.yml"), r"(?s)\n  alert:\n    needs: \[refresh, skill-coverage\]")

    def test_a_called_skill_coverage_leaves_the_alert_to_its_caller(self):
        self.assertIn("github.workflow == 'skill coverage'", self.text("skill-coverage.yml"))

    def test_the_mail_action_is_pinned_to_a_commit(self):
        self.assertRegex(self.text("failure-alert.yml"), r"uses: dawidd6/action-send-mail@[0-9a-f]{40}")


if __name__ == "__main__":
    unittest.main()
