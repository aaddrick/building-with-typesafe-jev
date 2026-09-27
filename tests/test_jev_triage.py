"""Jev's triage and verify, driven by a scripted Jev.

The fake answers stand in for the API, so these tests pin what code does with
each answer: the bands in jev_questions.py, the rule-10 backstops, failing
open when Jev is unavailable, and the decision trees drawn in the run page.
The questions themselves are checked against the skill's own rules.
"""

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
sys.path.insert(0, str(ROOT / "scripts"))
import jev_questions as Q  # noqa: E402
import jev_triage as T  # noqa: E402


def page(title, slug, body):
    return f"# {title}\nSource: https://docs.typesafe.ai/{slug}\n\n{body}\n\n"


FILLER = "\n".join(f"Unchanged line {i}." for i in range(40))
OLD = (page("Choice", "primitives/choice", f"{FILLER}\nPick one option from a list.\n{FILLER}")
       + page("Models", "models", "Jev answers fast.")
       + page("Legal", "legal", "Terms."))


def choice(value, confidence):
    return {"type": "choice", "choice": value, "confidence": confidence, "probabilities": {value: confidence}}


def score(value):
    return {"type": "score", "score": value, "confidence": 0.9, "legend": {}, "probabilities": {}}


def noul(p):
    return {"type": "noul", "noul": p}


def changed(kind="wording", conf=0.95, misleads=0.1, target="api-reference.md", tconf=0.9):
    return {"kind": choice(kind, conf), "misleads": score(misleads), "target": choice(target, tconf)}


class ScriptedJev:
    """Answers each request from `script`, keyed by the page title in its state."""

    def __init__(self, script, raise_for=()):
        self.script, self.raise_for, self.requests = script, raise_for, []

    def __call__(self, state, questions):
        self.requests.append((state, questions))
        title = (state.get("page") or {}).get("title") or state["docs"]["page"]
        if title in self.raise_for:
            raise self.raise_for[title]
        return {"model": "jev-1.13.0", "usage": {"input_tokens": 100}, "answers": self.script[title]}


def run_triage(new, script, old=OLD, skill=""):
    fake = ScriptedJev(script)
    return T.triage(old, new, skill, T.Jev(fake)), fake


def routes(tri):
    return {p["slug"]: (p["route"], p["by"]) for p in tri["pages"]}


class Triage(unittest.TestCase):
    def test_confident_wording_skips_claude(self):
        new = OLD.replace("Pick one option from a list.", "Choose one option from a list.")
        tri, fake = run_triage(new, {"Choice": changed()})
        self.assertEqual(routes(tri), {"primitives/choice": ("skip", "jev")})
        self.assertEqual(tri["route"], "skip")
        self.assertEqual(len(fake.requests), 1)

    def test_a_changed_fact_goes_to_claude_with_its_file(self):
        new = OLD.replace("Pick one option", "Pick one or more options")
        tri, _ = run_triage(new, {"Choice": changed("api_fact", 0.9, 1.8, "api-reference.md")})
        p = tri["pages"][0]
        self.assertEqual((p["route"], p["by"], p["target"]), ("update", "jev", "api-reference.md"))
        self.assertEqual(tri["route"], "focused")

    def test_a_changed_number_or_name_overrules_jev(self):
        new = OLD.replace("Pick one option from a list.", "Pick one option from a list of up to `512` options.")
        tri, _ = run_triage(new, {"Choice": changed("wording", 0.99, 0.0)})
        p = tri["pages"][0]
        self.assertEqual((p["route"], p["by"]), ("update", "code"))
        self.assertIn("`512`", p["reason"])

    def test_a_number_that_only_moves_is_not_a_changed_fact(self):
        self.assertEqual(T.changed_facts("Up to 255 options, fast.", "Fast, and up to 255 options."), [])
        self.assertEqual(T.changed_facts("up to 255", "up to 256"), ["255", "256"])

    def test_a_low_confidence_kind_or_other_is_left_to_claude(self):
        new = OLD.replace("Pick one option", "Select one option")
        for answers in (changed("guidance", 0.4), changed("other", 0.9)):
            tri, _ = run_triage(new, {"Choice": answers})
            self.assertEqual(tri["pages"][0]["route"], "unsure", answers)

    def test_wording_jev_is_not_sure_of_is_not_skipped(self):
        new = OLD.replace("Pick one option", "Select one option")
        tri, _ = run_triage(new, {"Choice": changed("wording", Q.SKIP_KIND_CONFIDENCE - 0.01)})
        self.assertNotEqual(tri["pages"][0]["route"], "skip")

    def test_wording_that_would_still_mislead_is_not_skipped(self):
        new = OLD.replace("Pick one option", "Select one option")
        tri, _ = run_triage(new, {"Choice": changed("wording", 0.95, misleads=1.2)})
        self.assertNotEqual(tri["pages"][0]["route"], "skip")

    def test_a_change_no_skill_file_would_hold_is_skipped(self):
        new = OLD.replace("Terms.", "New terms.")
        tri, _ = run_triage(new, {"Legal": changed("guidance", 0.7, 1.0, "none", 0.95)})
        self.assertEqual(routes(tri)["legal"], ("skip", "jev"))

    def test_added_pages_route_on_worth(self):
        script = {"Streaming": {"worth": noul(0.9), "target": choice("api-reference.md", 0.9)},
                  "Careers": {"worth": noul(0.05), "target": choice("none", 0.9)},
                  "Blog": {"worth": noul(0.5), "target": choice("patterns.md", 0.6)}}
        new = OLD + page("Streaming", "streaming", "Stream answers.") + page("Careers", "careers", "Join us.") \
            + page("Blog", "blog", "Musings.")
        tri, _ = run_triage(new, script)
        self.assertEqual(routes(tri), {"streaming": ("update", "jev"), "careers": ("skip", "jev"), "blog": ("unsure", "jev")})

    def test_removed_pages_are_decided_by_code_alone(self):
        new = page("Choice", "primitives/choice", f"{FILLER}\nPick one option from a list.\n{FILLER}")
        tri, fake = run_triage(new, {}, skill="See `models` for limits.")
        self.assertEqual(routes(tri), {"models": ("update", "code"), "legal": ("skip", "code")})
        self.assertEqual(fake.requests, [])

    def test_one_failed_call_leaves_that_page_to_claude(self):
        new = OLD.replace("Pick one", "Select one").replace("Terms.", "New terms.")
        fake = ScriptedJev({"Legal": changed()}, raise_for={"Choice": TimeoutError("slow")})
        tri = T.triage(OLD, new, "", T.Jev(fake))
        self.assertEqual(routes(tri)["primitives/choice"], ("unsure", "code"))
        self.assertEqual((tri["jev"]["errors"], tri["route"]), (1, "focused"))

    def test_without_a_key_the_run_fails_open_to_a_full_review(self):
        tri = T.triage(OLD, OLD.replace("Terms.", "New terms."), "", T.Jev(None))
        self.assertEqual(tri["route"], "full")
        self.assertIn("TYPESAFE_API_KEY", tri["why"])

    def test_a_refused_key_stops_asking(self):
        new = OLD.replace("Pick one", "Select one").replace("Terms.", "New terms.")
        fake = ScriptedJev({}, raise_for={"Choice": T.JevUnavailable("401"), "Legal": T.JevUnavailable("401")})
        tri = T.triage(OLD, new, "", T.Jev(fake))
        self.assertEqual(len(fake.requests), 1)
        self.assertEqual(tri["route"], "full")

    def test_a_forced_review_with_no_changes_is_a_full_review(self):
        tri, _ = run_triage(OLD, {})
        self.assertEqual((tri["route"], tri["pages"]), ("full", []))

    def test_jev_sees_the_change_not_the_whole_page(self):
        new = OLD.replace("Pick one option from a list.", "Choose one option from a list.")
        _, fake = run_triage(new, {"Choice": changed()})
        state, questions = fake.requests[0]
        self.assertEqual(questions, Q.CHANGED_PAGE_QUESTIONS)
        self.assertEqual(set(state), {"page", "change"})
        self.assertIn("Pick one option", state["change"]["before"])
        self.assertIn("Choose one option", state["change"]["after"])
        self.assertLess(state["change"]["after"].count("Unchanged line"), 2 * Q.CONTEXT_LINES + 1)

    def test_state_is_cut_to_stay_under_the_context_limit(self):
        self.assertLessEqual(len(T.cut("x" * 100_000)), Q.MAX_STATE_CHARS + 10)


class Verify(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.before = self.tmp / "before"
        self.before.mkdir()
        (self.before / "api-reference.md").write_text("Choice picks one option.\n")
        (self.before / "SKILL.md").write_text("See `models`.\n")
        self.after = self.tmp / "after"
        shutil.copytree(self.before, self.after)

    def edit(self, name="api-reference.md", text="Choice picks one or more options.\n"):
        (self.after / name).write_text(text)

    def run_verify(self, tri_pages, script, new=None):
        fake = ScriptedJev(script)
        tri = {"pages": tri_pages}
        new = new or OLD.replace("Pick one option", "Pick one or more options")
        return T.verify(tri, OLD, new, self.before, self.after, T.Jev(fake)), fake

    def choice_page(self, route="update", target="api-reference.md"):
        return {"slug": "primitives/choice", "title": "Choice", "status": "changed", "route": route, "target": target}

    def test_no_edits_is_unchanged_and_asks_nothing(self):
        ver, fake = self.run_verify([self.choice_page()], {})
        self.assertEqual(ver["verdict"], "unchanged")
        self.assertEqual(fake.requests, [])

    def test_an_edit_that_agrees_is_verified(self):
        self.edit()
        ver, fake = self.run_verify([self.choice_page()], {"Choice": {"conflict": noul(0.05), "covered": noul(0.9)}})
        self.assertEqual(ver["verdict"], "verified")
        state, questions = fake.requests[0]
        self.assertEqual(questions, Q.VERIFY_QUESTIONS)
        self.assertEqual(state["skill"]["file"], "api-reference.md")
        self.assertIn("one or more", state["skill"]["text"])

    def test_a_remaining_conflict_is_flagged(self):
        self.edit()
        ver, _ = self.run_verify([self.choice_page()], {"Choice": {"conflict": noul(0.8), "covered": noul(0.9)}})
        self.assertEqual((ver["verdict"], ver["checks"][0]["reason"]), ("flagged", "contradicts the docs"))

    def test_a_fact_page_must_show_the_new_form(self):
        self.edit()
        ver, _ = self.run_verify([self.choice_page()], {"Choice": {"conflict": noul(0.1), "covered": noul(0.2)}})
        self.assertEqual(ver["verdict"], "flagged")

    def test_an_unsure_page_only_needs_no_conflict(self):
        self.edit()
        ver, _ = self.run_verify([self.choice_page("unsure")], {"Choice": {"conflict": noul(0.1), "covered": noul(0.2)}})
        self.assertEqual(ver["verdict"], "verified")

    def test_skipped_pages_are_not_checked(self):
        self.edit()
        ver, fake = self.run_verify([self.choice_page("skip")], {})
        self.assertEqual((ver["verdict"], ver["checks"], fake.requests), ("verified", [], []))

    def test_a_skill_still_linking_a_removed_page_fails_by_code(self):
        self.edit()
        removed = {"slug": "models", "title": "Models", "status": "removed", "route": "update", "target": None}
        ver, _ = self.run_verify([removed], {})
        self.assertEqual((ver["verdict"], ver["checks"][0]["by"]), ("flagged", "code"))
        self.edit("SKILL.md", "No links.\n")
        ver, _ = self.run_verify([removed], {})
        self.assertEqual(ver["verdict"], "verified")

    def test_no_target_or_no_jev_means_unchecked_and_flagged(self):
        self.edit()
        ver, _ = self.run_verify([self.choice_page(target=None)], {})
        self.assertEqual((ver["verdict"], ver["checks"][0]["result"]), ("flagged", "unchecked"))
        ver = T.verify({"pages": [self.choice_page()]}, OLD, OLD, self.before, self.after, T.Jev(None))
        self.assertEqual((ver["verdict"], ver["checks"][0]["result"]), ("flagged", "unchecked"))


class Rendering(unittest.TestCase):
    def tri(self, n=3):
        pages = [{"slug": f"p{i}", "title": f"P{i}", "status": "changed", "route": ["skip", "update", "unsure"][i % 3],
                  "by": "jev", "target": "api-reference.md", "reason": "r", "edge": "wording 0.95 · misleads 0.1"}
                 for i in range(n)]
        return {"route": "focused", "why": "w", "pages": pages, "jev": {"calls": n, "model": "jev-1.13.0",
                "input_tokens": 1000, "errors": 0, "unavailable": None}}

    def test_the_triage_tree_has_a_branch_per_page_into_the_run_route(self):
        tree = T.triage_tree(self.tri())
        self.assertTrue(tree.startswith("```mermaid\nflowchart LR\n"))
        self.assertEqual(len(re.findall(r"--> run$", tree, re.M)), 3)
        self.assertIn(T.RUN_ROUTES["focused"], tree)
        for route in ("skip", "update", "unsure"):
            self.assertIn(f":::{route}", tree)

    def test_a_big_triage_folds_its_skipped_pages(self):
        tree = T.triage_tree(self.tri(60))
        self.assertIn("20 more page(s)", tree)
        self.assertLess(tree.count("--> run"), 60)

    def test_labels_cannot_break_the_diagram(self):
        self.assertNotIn('"', T.label('say "hi" | <b>'))
        self.assertNotIn("|", T.label("a|b"))

    def test_the_verify_tree_ends_in_the_verdict(self):
        ver = {"verdict": "flagged", "why": "1 doubt(s)", "jev": {}, "checks": [
            {"slug": "p0", "target": "SKILL.md", "result": "doubt", "by": "jev", "edge": "conflict 0.80 · covered 0.90"}]}
        tree = T.verify_tree(ver)
        self.assertIn(":::doubt", tree)
        self.assertIn("Flagged", tree)

    def test_the_focus_prompt_groups_pages_by_route(self):
        text = T.focus_prompt(self.tri())
        self.assertLess(text.index("Pages to act on"), text.index("unsure"))
        self.assertIn("- `p1`", text)
        self.assertIn("Review every change", T.focus_prompt({**self.tri(), "route": "full", "why": "no key"}))

    def verdict(self, verdict="flagged"):
        return {"verdict": verdict, "why": "w", "jev": {}, "checks": [
            {"slug": "p1", "target": "api-reference.md", "result": "doubt" if verdict == "flagged" else "ok",
             "by": "jev", "edge": "conflict 0.10 · covered 0.30"}]}

    def edges(self, tree):
        return re.findall(r"^  (\S+) (==>|-\.->)(?: \|[^|]*\|)? (\w+)", tree, re.M)

    def test_the_flow_draws_every_branch_and_marks_the_path_taken(self):
        tree = T.flow_tree(self.tri(), self.verdict())
        for key in T.RUN_ROUTES:
            self.assertIn(f"route_{key}", tree)
        for key in T.VERDICTS:
            self.assertIn(f"verdict_{key}", tree)
        self.assertIn("route_focused{{", tree)
        self.assertRegex(tree, r'route_focused\{\{"[^"]+"\}\}:::taken')
        self.assertRegex(tree, r'route_skip\{\{"[^"]+"\}\}:::idle')
        self.assertRegex(tree, r"verdict_flagged\(\[\"[^\"]+\"\]\):::taken")
        solid = {(a, b) for a, kind, b in self.edges(tree) if kind == "==>"}
        dotted = {(a, b) for a, kind, b in self.edges(tree) if kind == "-.->"}
        self.assertIn(("route_focused", "claude"), solid)
        self.assertIn(("route_full", "claude"), dotted)
        self.assertIn(("route_skip", "record"), dotted)
        self.assertIn(("jt", "route_skip"), dotted)
        self.assertNotIn(("jt", "route_focused"), dotted)
        self.assertIn(("v0", "verdict_flagged"), solid)
        self.assertIn(("claude", "verdict_verified"), dotted)

    def test_a_skipped_run_never_reaches_claude_or_a_verdict(self):
        tri = {**self.tri(), "route": "skip"}
        tree = T.flow_tree(tri)
        self.assertRegex(tree, r"claude\[\"[^\"]+\"\]:::idle")
        self.assertRegex(tree, r"record\(\[\"[^\"]+\"\]\):::taken")
        self.assertNotIn("verdict_", tree)

    def test_a_run_with_no_edits_goes_straight_to_its_verdict(self):
        tree = T.flow_tree(self.tri(), {"verdict": "unchanged", "why": "w", "jev": {}, "checks": []})
        solid = {(a, b) for a, kind, b in self.edges(tree) if kind == "==>"}
        self.assertIn(("claude", "verdict_unchanged"), solid)

    def test_the_flow_command_writes_markdown_with_or_without_verify(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        (tmp / "t.json").write_text(json.dumps(self.tri()))
        T.main(["flow", "--triage", str(tmp / "t.json"), "--verify", str(tmp / "missing.json"), "--out", str(tmp / "f.md")])
        text = (tmp / "f.md").read_text()
        self.assertTrue(text.startswith("### How this review ran\n\n```mermaid\n"))
        self.assertIn("Solid arrows", text)

    def test_the_tally_prices_input_tokens(self):
        self.assertIn("$0.00004", T.tally_line(self.tri()["jev"]))


class Commands(unittest.TestCase):
    """The CLI as the workflow runs it, with no key, so it takes the fail-open path."""

    def run_cli(self, args):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        outputs, summary = tmp / "out.txt", tmp / "summary.md"
        env = {k: v for k, v in os.environ.items() if k != "TYPESAFE_API_KEY"}
        env.update(GITHUB_OUTPUT=str(outputs), GITHUB_STEP_SUMMARY=str(summary))
        result = subprocess.run([sys.executable, str(ROOT / "scripts/jev_triage.py"), *args(tmp)],
                                capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        found = dict(re.findall(r"^(\w+)<<__OUTPUT__\n(.*?)\n__OUTPUT__$", outputs.read_text(), re.M | re.S))
        return found, summary.read_text(), tmp

    def test_triage_without_a_key_routes_to_a_full_review_and_writes_its_files(self):
        def args(tmp):
            (tmp / "old.txt").write_text(OLD)
            (tmp / "new.txt").write_text(OLD.replace("Terms.", "New terms."))
            return ["triage", "--old", str(tmp / "old.txt"), "--new", str(tmp / "new.txt"),
                    "--skill", str(ROOT / "skills/building-with-typesafe-jev"), "--out-dir", str(tmp / "out")]
        outputs, summary, tmp = self.run_cli(args)
        self.assertEqual((outputs["route"], outputs["pages"]), ("full", "1"))
        self.assertIn("```mermaid", summary)
        for name in ("triage.json", "focus.md", "jev-triage.md", "skip-summary.md"):
            self.assertTrue((tmp / "out" / name).is_file(), name)
        self.assertEqual(json.loads((tmp / "out/triage.json").read_text())["route"], "full")

    def test_verify_with_no_edits_is_unchanged(self):
        def args(tmp):
            (tmp / "t.json").write_text(json.dumps({"pages": []}))
            (tmp / "d.txt").write_text(OLD)
            skill = str(ROOT / "skills/building-with-typesafe-jev")
            return ["verify", "--triage", str(tmp / "t.json"), "--old", str(tmp / "d.txt"), "--new", str(tmp / "d.txt"),
                    "--skill-before", skill, "--skill-after", skill, "--out-dir", str(tmp / "v")]
        outputs, summary, _ = self.run_cli(args)
        self.assertEqual(outputs["verdict"], "unchanged")
        self.assertIn("No edits", summary)


class Questions(unittest.TestCase):
    """The pipeline's own questions follow the rules the skill teaches."""

    ALL = {**Q.CHANGED_PAGE_QUESTIONS, **Q.ADDED_PAGE_QUESTIONS, **Q.VERIFY_QUESTIONS}

    def test_choices_offer_a_way_out_and_use_the_same_keys_on_every_option(self):
        for name, q in self.ALL.items():
            if q["type"] != "choice":
                continue
            options = q["criteria"]
            self.assertTrue({"other", "none"} & set(options), f"{name} needs an other or none option (rule 8)")
            self.assertLessEqual(len(options), 255)
            self.assertEqual(len({tuple(sorted(v)) for v in options.values()}), 1, f"{name} option keys differ (rule 8)")

    def test_scores_have_two_to_ten_situations(self):
        for q in self.ALL.values():
            if q["type"] == "score":
                self.assertTrue(2 <= len(q["criteria"]) <= 10)
                for level in q["criteria"]:
                    self.assertNotRegex(level.lower(), r"^(low|medium|high|moderate|\d)$", "rule 7: a situation, not a degree")

    def test_nouls_are_phrased_so_high_means_yes(self):
        for q in self.ALL.values():
            if q["type"] == "noul":
                self.assertTrue(q["instructions"].startswith(("Does", "Is", "Has")), q["instructions"])
                self.assertNotRegex(q["instructions"], r"\bnot\b", "rule 9: no negated Noul")

    def test_questions_point_at_state_paths_that_exist(self):
        paths = {
            "kind": {"page.title", "change.before", "change.after"},
            "misleads": {"change.before", "change.after"},
            "target": set(),
            "worth": {"page.text"},
            "conflict": {"skill.text", "docs.after"},
            "covered": {"skill.text", "docs.before", "docs.after"},
        }
        states = {"page": {"title", "text"}, "change": {"before", "after"}, "docs": {"page", "before", "after"},
                  "skill": {"file", "text"}}
        for name, q in self.ALL.items():
            text = q["instructions"] + json.dumps(q.get("criteria"))
            used = set(re.findall(r"`(\w+\.\w+)`", text))
            self.assertEqual(used, paths[name], name)
            for path in used:
                top, key = path.split(".")
                self.assertIn(key, states[top], path)

    def test_the_model_is_pinned(self):
        self.assertRegex(Q.MODEL, r"^jev-\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()
