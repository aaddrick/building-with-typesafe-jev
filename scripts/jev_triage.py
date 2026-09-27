#!/usr/bin/env python3
"""Jev's two decisions in the docs pipeline: triage before Claude, verify after.

Claude is the expensive step, and most docs changes are rewording. So Jev
reads each changed or added page first and code routes it: skip it, send it
to Claude, or send it with a note that Jev was unsure. When every page is
skipped, Claude never runs. After Claude edits, Jev reads each page it was
sent against the edited skill file and flags any that still disagree.

Code owns every decision; Jev answers narrow questions. The questions and
thresholds are in jev_questions.py. Code also backstops Jev (rule 10): a
change to a number or a backticked name always goes to Claude, and a skill
that still links a removed page always fails verify.

Commands (each writes step outputs, a Mermaid decision tree to the step
summary, and Markdown for the pull request):
  triage  --old OLD --new NEW --skill DIR --out-dir DIR
  verify  --triage FILE --old OLD --new NEW --skill-before DIR --skill-after DIR --out-dir DIR
  flow    --triage FILE [--verify FILE] --out FILE   (the whole run as one tree, for the PR)

Without TYPESAFE_API_KEY or the typesafe-sdk package, triage routes the run
to a full Claude review and verify reports every page as unchecked: the
pipeline fails open, never shut.
"""

import argparse
import difflib
import filecmp
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import docs_diff  # noqa: E402
import jev_questions as Q  # noqa: E402
from docs_pipeline import set_outputs, step_summary  # noqa: E402

# What rule 10 treats as a fact: a backticked name or a number.
FACT = re.compile(r"`[^`\n]+`|(?<![\w.])\d+(?:[.,]\d+)*(?![\w])")
ROUTE_ICON = {"skip": "⏭️", "update": "✍️", "unsure": "❓"}
RUN_ROUTES = {
    "skip": "⏭️ Wording only · skip Claude",
    "focused": "🎯 Facts changed · focused Claude review",
    "full": "🛟 Full Claude review",
}


class JevUnavailable(Exception):
    """No key, no SDK, or a key the API refuses: stop asking for this run."""


class Jev:
    """Asks Jev through `ask(state, questions) -> response dict` and keeps the run's tally."""

    def __init__(self, ask):
        self.ask = ask
        self.unavailable = None if ask else "TYPESAFE_API_KEY is not set"
        self.model = None
        self.calls = 0
        self.errors = 0
        self.input_tokens = 0

    def __call__(self, state: dict, questions: dict) -> dict | None:
        if self.unavailable:
            return None
        try:
            response = self.ask(state, questions)
        except JevUnavailable as exc:
            self.unavailable = str(exc)
            return None
        except Exception as exc:  # one page's failure leaves that page to Claude
            self.errors += 1
            print(f"::warning::Jev call failed: {type(exc).__name__}: {exc}")
            return None
        self.calls += 1
        self.model = response.get("model") or self.model
        self.input_tokens += (response.get("usage") or {}).get("input_tokens", 0)
        return response["answers"]

    def tally(self) -> dict:
        return {"model": self.model, "calls": self.calls, "errors": self.errors,
                "input_tokens": self.input_tokens, "unavailable": self.unavailable}


def sdk_asker():
    """An ask function backed by typesafe-sdk, or None when there is no key."""
    if not os.environ.get("TYPESAFE_API_KEY"):
        return None
    try:
        from typesafe_sdk import (TypeSafeAuthenticationError, TypeSafeClient,
                                  TypeSafeError, TypeSafePermissionDeniedError)
    except ImportError:
        def missing(state, questions):
            raise JevUnavailable("the typesafe-sdk package is not installed")
        return missing
    try:
        # One client for the whole run; the SDK retries 429 and 5xx itself.
        client = TypeSafeClient(model=os.environ.get("JEV_MODEL") or Q.MODEL)
    except TypeSafeError as exc:
        def refused(state, questions):
            raise JevUnavailable(f"the client could not start: {exc}")
        return refused

    def ask(state, questions):
        try:
            return client.system_one(state=state, questions=questions).model_dump(mode="json")
        except (TypeSafeAuthenticationError, TypeSafePermissionDeniedError) as exc:
            raise JevUnavailable(f"the API refused the key ({type(exc).__name__})") from exc
    return ask


# State


def cut(text: str) -> str:
    return text if len(text) <= Q.MAX_STATE_CHARS else text[: Q.MAX_STATE_CHARS] + "\n[cut]"


def changed_regions(before: str, after: str) -> tuple[str, str]:
    """The changed stretches of a page, with a little context, as (before, after) text."""
    a, b = before.splitlines(), after.splitlines()
    olds, news = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        c = Q.CONTEXT_LINES
        olds.append("\n".join(a[max(0, i1 - c): i2 + c]))
        news.append("\n".join(b[max(0, j1 - c): j2 + c]))
    return cut("\n[...]\n".join(olds)), cut("\n[...]\n".join(news))


def changed_facts(before: str, after: str) -> list[str]:
    """Numbers and backticked names on one side of a change and not the other."""
    old, new = set(FACT.findall(before)), set(FACT.findall(after))
    return sorted(old ^ new)


# Triage


def triage_changed(slug, title, before, after, jev) -> dict:
    region_before, region_after = changed_regions(before, after)
    facts = changed_facts(region_before, region_after)
    answers = jev({"page": {"title": title}, "change": {"before": region_before, "after": region_after}},
                  Q.CHANGED_PAGE_QUESTIONS)
    page = {"slug": slug, "title": title, "status": "changed", "answers": answers, "facts": facts}
    target = None
    if answers:
        kind, misleads, tgt = answers["kind"], answers["misleads"], answers["target"]
        target = tgt["choice"] if tgt["choice"] != "none" else None
        page["edge"] = f"{kind['choice']} {kind['confidence']:.2f} · misleads {misleads['score']:.1f}"
    page["target"] = target
    if facts:
        # Rule 10: Jev may make this stricter, never looser.
        shown = ", ".join(facts[:4]) + (" …" if len(facts) > 4 else "")
        # The tree shows Jev's answer beside the rule that overrode it.
        jev_said = f" · Jev said {page['edge'].split(' · ')[0]}" if answers else ""
        return {**page, "route": "update", "by": "code", "reason": f"names or numbers changed: {shown}",
                "edge": f"changed {shown}{jev_said}"}
    if not answers:
        return {**page, "route": "unsure", "by": "code", "reason": "Jev did not answer", "edge": "no answer"}
    if kind["choice"] in ("wording", "example_only") and kind["confidence"] >= Q.SKIP_KIND_CONFIDENCE \
            and misleads["score"] < Q.SKIP_MAX_MISLEADS:
        return {**page, "route": "skip", "by": "jev", "reason": f"{kind['choice']}, same code either way"}
    if tgt["choice"] == "none" and tgt["confidence"] >= Q.SKIP_TARGET_CONFIDENCE:
        return {**page, "route": "skip", "by": "jev", "reason": "nothing a coding agent needs"}
    if kind["choice"] == "other" or kind["confidence"] < Q.UNSURE_KIND_CONFIDENCE:
        return {**page, "route": "unsure", "by": "jev", "reason": f"unsure of the kind ({kind['choice']} {kind['confidence']:.2f})"}
    return {**page, "route": "update", "by": "jev", "reason": kind["choice"].replace("_", " ")}


def triage_added(slug, title, text, jev) -> dict:
    answers = jev({"page": {"title": title, "text": cut(text)}}, Q.ADDED_PAGE_QUESTIONS)
    page = {"slug": slug, "title": title, "status": "added", "answers": answers, "facts": []}
    if not answers:
        return {**page, "target": None, "route": "unsure", "by": "code", "reason": "Jev did not answer", "edge": "no answer"}
    worth, tgt = answers["worth"]["noul"], answers["target"]
    target = tgt["choice"] if tgt["choice"] != "none" else None
    page.update(target=target, edge=f"worth {worth:.2f} · {tgt['choice']}")
    if worth >= Q.ADD_WORTH:
        return {**page, "route": "update", "by": "jev", "reason": "new page with something to teach"}
    if worth <= Q.SKIP_WORTH:
        return {**page, "route": "skip", "by": "jev", "reason": "new page with nothing to teach"}
    return {**page, "route": "unsure", "by": "jev", "reason": f"unsure it teaches anything ({worth:.2f})"}


def triage_removed(slug, title, skill: str) -> dict:
    linked = docs_diff.referenced(slug, skill)
    return {
        "slug": slug, "title": title, "status": "removed", "answers": None, "facts": [], "target": None,
        "route": "update" if linked else "skip", "by": "code",
        "reason": "the skill links this removed page" if linked else "the skill never linked it",
        "edge": "page removed, " + ("linked" if linked else "not linked"),
    }


def triage(old_text: str, new_text: str, skill: str, jev: Jev) -> dict:
    old, new = docs_diff.split_pages(old_text), docs_diff.split_pages(new_text)
    pages = []
    for slug in sorted(new.keys() | old.keys()):
        if slug not in old:
            pages.append(triage_added(slug, new[slug][0], new[slug][1], jev))
        elif slug not in new:
            pages.append(triage_removed(slug, old[slug][0], skill))
        elif old[slug][1] != new[slug][1]:
            pages.append(triage_changed(slug, new[slug][0], old[slug][1], new[slug][1], jev))
    if jev.unavailable:
        route, why = "full", f"Jev unavailable: {jev.unavailable}"
    elif not pages:
        route, why = "full", "no page changed; a forced review reads everything"
    elif all(p["route"] == "skip" for p in pages):
        route, why = "skip", "every change is wording, examples, or off-topic"
    else:
        n = sum(p["route"] != "skip" for p in pages)
        route, why = "focused", f"{n} of {len(pages)} pages need Claude"
    return {"route": route, "why": why, "pages": pages, "jev": jev.tally()}


# Verify


def read_skill(skill_dir: Path) -> dict[str, str]:
    return {str(p.relative_to(skill_dir)): p.read_text(encoding="utf-8") for p in sorted(skill_dir.rglob("*.md"))}


def same_tree(a: Path, b: Path) -> bool:
    cmp = filecmp.dircmp(a, b)
    if cmp.left_only or cmp.right_only or cmp.funny_files:
        return False
    if filecmp.cmpfiles(a, b, cmp.common_files, shallow=False)[1:] != ([], []):
        return False
    return all(same_tree(a / d, b / d) for d in cmp.common_dirs)


def verify(tri: dict, old_text: str, new_text: str, before_dir: Path, after_dir: Path, jev: Jev) -> dict:
    if same_tree(before_dir, after_dir):
        return {"verdict": "unchanged", "why": "Claude made no edits", "checks": [], "jev": jev.tally()}
    old, new = docs_diff.split_pages(old_text), docs_diff.split_pages(new_text)
    after = read_skill(after_dir)
    all_after = "\n".join(after.values())
    checks = []
    for page in tri["pages"]:
        if page["route"] == "skip":
            continue
        check = {"slug": page["slug"], "target": page["target"], "answers": None}
        if page["status"] == "removed":
            linked = docs_diff.referenced(page["slug"], all_after)
            checks.append({**check, "result": "doubt" if linked else "ok", "by": "code",
                           "reason": "still links the removed page" if linked else "link dropped",
                           "edge": "still linked" if linked else "link dropped"})
            continue
        if page["target"] not in after:
            checks.append({**check, "result": "unchecked", "by": "code", "reason": "no skill file to check against",
                           "edge": "no target"})
            continue
        if page["status"] == "added":
            docs_before, docs_after = "", cut(new[page["slug"]][1])
        else:
            docs_before, docs_after = changed_regions(old[page["slug"]][1], new[page["slug"]][1])
        answers = jev({"docs": {"page": page["title"], "before": docs_before, "after": docs_after},
                       "skill": {"file": page["target"], "text": cut(after[page["target"]])}}, Q.VERIFY_QUESTIONS)
        check["answers"] = answers
        if not answers:
            checks.append({**check, "result": "unchecked", "by": "code", "reason": "Jev did not answer", "edge": "no answer"})
            continue
        conflict, covered = answers["conflict"]["noul"], answers["covered"]["noul"]
        # Only a page Jev or code said carries a fact must show the new form.
        need_cover = page["route"] == "update"
        ok = conflict <= Q.MAX_CONFLICT and (covered >= Q.MIN_COVERED or not need_cover)
        reason = "agrees with the docs" if ok else (
            "contradicts the docs" if conflict > Q.MAX_CONFLICT else "does not state the new form")
        checks.append({**check, "result": "ok" if ok else "doubt", "by": "jev", "reason": reason,
                       "edge": f"conflict {conflict:.2f} · covered {covered:.2f}"})
    doubts = sum(c["result"] == "doubt" for c in checks)
    unchecked = sum(c["result"] == "unchecked" for c in checks)
    if doubts or unchecked:
        verdict = "flagged"
        why = ", ".join(s for s in (f"{doubts} doubt(s)" if doubts else "", f"{unchecked} unchecked" if unchecked else "") if s)
    else:
        verdict, why = "verified", f"{len(checks)} page(s) agree with the docs"
    return {"verdict": verdict, "why": why, "checks": checks, "jev": jev.tally()}


# Rendering


def label(text: str) -> str:
    """Text safe inside a quoted Mermaid label."""
    return (str(text).replace("&", "&amp;").replace('"', "#quot;").replace("<", "&lt;")
            .replace(">", "&gt;").replace("|", "&#124;"))


def mermaid(lines: list[str]) -> str:
    styles = [
        "classDef skip fill:#f1f5f9,stroke:#94a3b8,color:#475569",
        "classDef update fill:#dbeafe,stroke:#2563eb,color:#1e3a8a",
        "classDef unsure fill:#fef3c7,stroke:#d97706,color:#78350f",
        "classDef ok fill:#dcfce7,stroke:#16a34a,color:#14532d",
        "classDef doubt fill:#fee2e2,stroke:#dc2626,color:#7f1d1d",
        "classDef run fill:#ede9fe,stroke:#7c3aed,color:#3b0764,font-weight:bold",
        "classDef taken fill:#ede9fe,stroke:#7c3aed,stroke-width:3px,color:#3b0764,font-weight:bold",
        "classDef idle fill:#f8fafc,stroke:#cbd5e1,stroke-dasharray:4 3,color:#94a3b8",
    ]
    return "```mermaid\nflowchart LR\n" + "\n".join("  " + s for s in styles + lines) + "\n```\n"


# Past this many pages, the tree folds skipped pages into one node.
MAX_TREE_PAGES = 25


def triage_tree(tri: dict) -> str:
    pages = tri["pages"]
    shown = pages if len(pages) <= MAX_TREE_PAGES else [p for p in pages if p["route"] != "skip"]
    folded = len(pages) - len(shown)
    lines = [f'start(["🧠 Jev triage · {len(pages)} page(s)"]):::run']
    for i, p in enumerate(shown):
        who = "Jev" if p["by"] == "jev" else "code"
        dest = f"{ROUTE_ICON[p['route']]} {p['route']}" + (f" → {p['target']}" if p["route"] != "skip" and p["target"] else "")
        lines += [
            f'start --> p{i}["{label(p["slug"])}<br/>({p["status"]})"]',
            f'p{i} -->|"{label(who + " · " + p.get("edge", p["reason"]))}"| r{i}(["{label(dest)}"]):::{p["route"]}',
            f"r{i} --> run",
        ]
    if folded:
        lines += [f'start --> folded["{folded} more page(s)"]', f'folded -->|"Jev"| fr(["⏭️ skip"]):::skip', "fr --> run"]
    lines.append(f'run{{{{"{label(RUN_ROUTES[tri["route"]])}"}}}}:::run')
    if not pages:
        lines.append("start --> run")
    return mermaid(lines)


def verify_tree(ver: dict) -> str:
    icon = {"ok": "✅ agrees", "doubt": "⚠️ doubt", "unchecked": "❔ unchecked"}
    style = {"ok": "ok", "doubt": "doubt", "unchecked": "unsure"}
    lines = [f'start(["🔎 Jev verify · {len(ver["checks"])} page(s)"]):::run']
    for i, c in enumerate(ver["checks"]):
        name = c["slug"] + (f" → {c['target']}" if c["target"] else "")
        who = "Jev" if c["by"] == "jev" else "code"
        lines += [
            f'start --> c{i}["{label(name)}"]',
            f'c{i} -->|"{label(who + " · " + c["edge"])}"| v{i}(["{icon[c["result"]]}"]):::{style[c["result"]]}',
            f"v{i} --> verdict",
        ]
    title = {"verified": "✅ Verified · open the PR", "flagged": "⚠️ Flagged · open the PR for a human check",
             "unchanged": "🟰 No edits · record the review"}[ver["verdict"]]
    lines.append(f'verdict{{{{"{label(title + " · " + ver["why"])}"}}}}:::run')
    if not ver["checks"]:
        lines.append("start --> verdict")
    return mermaid(lines)


VERDICTS = {
    "verified": "✅ Jev verified · open the PR",
    "flagged": "⚠️ Jev doubts · PR for a human check",
    "unchanged": "🟰 No edits · record the review",
}


def flow_tree(tri: dict, ver: dict | None = None) -> str:
    """The whole run as one tree for the pull request: every branch drawn, the path taken solid."""
    pages = tri["pages"]
    shown = pages if len(pages) <= MAX_TREE_PAGES else [p for p in pages if p["route"] != "skip"]
    folded = len(pages) - len(shown)
    route = tri["route"]
    ran_claude = route != "skip"

    def arrow(taken):
        return "==>" if taken else "-.->"

    def cls(taken):
        return "taken" if taken else "idle"

    lines = [f'docs(["📄 Docs changed · {len(pages)} page(s)"]):::run', 'subgraph jt["🧠 Jev triage"]']
    for i, p in enumerate(shown):
        who = "Jev" if p["by"] == "jev" else "code"
        dest = f"{ROUTE_ICON[p['route']]} {p['route']}" + (f" → {p['target']}" if p["route"] != "skip" and p["target"] else "")
        lines += [f'p{i}["{label(p["slug"])}<br/>({p["status"]})"]',
                  f'p{i} -->|"{label(who + " · " + p.get("edge", p["reason"]))}"| r{i}(["{label(dest)}"]):::{p["route"]}']
    if folded:
        lines += [f'folded["{folded} more page(s)"]', 'folded -->|"Jev"| fr(["⏭️ skip"]):::skip']
    lines.append("end")
    leaves = [f"r{i}" for i in range(len(shown))] + (["fr"] if folded else [])
    lines += [f"docs --> p{i}" for i in range(len(shown))] + (["docs --> folded"] if folded else [])
    for key, text in RUN_ROUTES.items():
        lines.append(f'route_{key}{{{{"{label(text)}"}}}}:::{cls(key == route)}')
    lines += [f"{leaf} ==> route_{route}" for leaf in leaves] or [f"docs ==> route_{route}"]
    # Branches not taken hang off the triage box, so they read as the other ways out.
    lines += [f"jt -.-> route_{key}" for key in RUN_ROUTES if key != route]
    lines += [
        f'claude["✍️ Claude · edit the skill"]:::{cls(ran_claude)}',
        f"route_focused {arrow(route == 'focused')} claude",
        f"route_full {arrow(route == 'full')} claude",
        f'record(["🟰 Record the review, or update the open PR"]):::{cls(not ran_claude)}',
        f"route_skip {arrow(route == 'skip')} record",
    ]
    if ran_claude:
        verdict = ver["verdict"] if ver else None
        for key, text in VERDICTS.items():
            lines.append(f'verdict_{key}(["{label(text)}"]):::{cls(key == verdict)}')
        checks = ver["checks"] if ver else []
        if checks:
            icon = {"ok": "✅ agrees", "doubt": "⚠️ doubt", "unchecked": "❔ unchecked"}
            style = {"ok": "ok", "doubt": "doubt", "unchecked": "unsure"}
            lines.append('subgraph jv["🔎 Jev verify"]')
            for i, c in enumerate(checks):
                name = c["slug"] + (f" → {c['target']}" if c["target"] else "")
                who = "Jev" if c["by"] == "jev" else "code"
                lines += [f'c{i}["{label(name)}"]',
                          f'c{i} -->|"{label(who + " · " + c["edge"])}"| v{i}(["{icon[c["result"]]}"]):::{style[c["result"]]}']
            lines.append("end")
            lines += [f"claude ==> c{i}" for i in range(len(checks))]
            lines += [f"v{i} ==> verdict_{verdict}" for i in range(len(checks))]
            lines += [f"claude -.-> verdict_{k}" for k in VERDICTS if k != verdict]
        else:
            lines += [f"claude {arrow(k == verdict)} verdict_{k}" for k in VERDICTS]
    return mermaid(lines)


def flow_markdown(tri: dict, ver: dict | None) -> str:
    return ("### How this review ran\n\n" + flow_tree(tri, ver)
            + "\nSolid arrows are the path this run took; dotted ones are the branches it did not.\n")


def tally_line(jev: dict) -> str:
    if jev.get("unavailable"):
        return f"Jev unavailable: {jev['unavailable']}."
    cost = jev["input_tokens"] * 0.042 / 1_000_000
    return (f"{jev['calls']} Jev call(s) on `{jev['model'] or 'n/a'}`, {jev['input_tokens']:,} input tokens "
            f"(about ${cost:.5f}), {jev['errors']} error(s).")


def triage_table(tri: dict) -> str:
    rows = ["| Page | Change | Decided by | Route | Why |", "|---|---|---|---|---|"]
    for p in tri["pages"]:
        target = f" → `{p['target']}`" if p["route"] != "skip" and p["target"] else ""
        rows.append(f"| `{p['slug']}` | {p['status']} | {p['by']}{' · ' + p['edge'] if p.get('edge') else ''} "
                    f"| {ROUTE_ICON[p['route']]} {p['route']}{target} | {p['reason']} |")
    return "\n".join(rows) + "\n"


def verify_table(ver: dict) -> str:
    rows = ["| Page | Skill file | Checked by | Result | Why |", "|---|---|---|---|---|"]
    for c in ver["checks"]:
        rows.append(f"| `{c['slug']}` | {('`' + c['target'] + '`') if c['target'] else '—'} | {c['by']} · {c['edge']} "
                    f"| {c['result']} | {c['reason']} |")
    return "\n".join(rows) + "\n"


def focus_prompt(tri: dict) -> str:
    """The section of Claude's prompt that passes on Jev's triage."""
    head = "## Jev triage\n\n"
    if tri["route"] == "full":
        return head + f"Jev did not triage this run ({tri['why']}). Review every change in the report.\n"
    out = [head + "Jev, a fast classifier, read every change before you. Code routed each page from its answers. "
           "Treat the routing as a strong hint: act on the pages sent to you, and overrule a skipped page only "
           "if its diff clearly changes a fact.\n"]
    for route, heading in (("update", "Pages to act on"), ("unsure", "Pages Jev was unsure about: decide yourself"),
                           ("skip", "Pages Jev judged need no skill edit")):
        chosen = [p for p in tri["pages"] if p["route"] == route]
        if chosen:
            out.append(f"### {heading}\n")
            out += [f"- `{p['slug']}` ({p['status']}): {p['reason']}" + (f"; likely file `{p['target']}`" if p["target"] and route != "skip" else "")
                    for p in chosen]
            out.append("")
    return "\n".join(out)


# Commands


def cmd_triage(args) -> None:
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tri = triage(Path(args.old).read_text(encoding="utf-8") if Path(args.old).is_file() else "",
                 Path(args.new).read_text(encoding="utf-8"), docs_diff.skill_text(Path(args.skill)), Jev(sdk_asker()))
    (out / "triage.json").write_text(json.dumps(tri, indent=2), encoding="utf-8")
    (out / "focus.md").write_text(focus_prompt(tri), encoding="utf-8")
    (out / "jev-triage.md").write_text(
        f"### Triaged by Jev\n\n{tally_line(tri['jev'])} Route: **{RUN_ROUTES[tri['route']]}** ({tri['why']}).\n\n"
        + triage_table(tri), encoding="utf-8")
    (out / "skip-summary.md").write_text(
        "### Skill changes\n\nNone. Jev triaged every change as wording, examples, or off-topic, so Claude was not called.\n",
        encoding="utf-8")
    step_summary(f"## 🧠 Jev triage\n\n{tally_line(tri['jev'])}\n\n{triage_tree(tri)}\n{triage_table(tri)}")
    counts = {r: sum(p["route"] == r for p in tri["pages"]) for r in ("skip", "update", "unsure")}
    set_outputs(route=tri["route"], why=tri["why"], pages=len(tri["pages"]), **counts)


def cmd_verify(args) -> None:
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    tri = json.loads(Path(args.triage).read_text(encoding="utf-8"))
    ver = verify(tri, Path(args.old).read_text(encoding="utf-8") if Path(args.old).is_file() else "",
                 Path(args.new).read_text(encoding="utf-8"), Path(args.skill_before), Path(args.skill_after),
                 Jev(sdk_asker()))
    (out / "verify.json").write_text(json.dumps(ver, indent=2), encoding="utf-8")
    body = f"### Checked by Jev\n\n{tally_line(ver['jev'])} Verdict: **{ver['verdict']}** ({ver['why']}).\n\n"
    if ver["checks"]:
        body += verify_table(ver)
    (out / "jev-verify.md").write_text(body, encoding="utf-8")
    step_summary(f"## 🔎 Jev verify\n\n{tally_line(ver['jev'])}\n\n{verify_tree(ver)}\n" + (verify_table(ver) if ver["checks"] else ""))
    set_outputs(verdict=ver["verdict"], why=ver["why"], doubts=sum(c["result"] != "ok" for c in ver["checks"]))


def cmd_flow(args) -> None:
    tri = json.loads(Path(args.triage).read_text(encoding="utf-8"))
    ver = json.loads(Path(args.verify).read_text(encoding="utf-8")) if args.verify and Path(args.verify).is_file() else None
    Path(args.out).write_text(flow_markdown(tri, ver), encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("triage")
    p.add_argument("--old", required=True, help="the reviewed copy; a missing file means none")
    p.add_argument("--new", required=True)
    p.add_argument("--skill", required=True)
    p.add_argument("--out-dir", required=True)
    p.set_defaults(func=cmd_triage)
    p = sub.add_parser("verify")
    p.add_argument("--triage", required=True)
    p.add_argument("--old", required=True)
    p.add_argument("--new", required=True)
    p.add_argument("--skill-before", required=True)
    p.add_argument("--skill-after", required=True)
    p.add_argument("--out-dir", required=True)
    p.set_defaults(func=cmd_verify)
    p = sub.add_parser("flow", help="draw the whole run as one Mermaid tree for the pull request")
    p.add_argument("--triage", required=True)
    p.add_argument("--verify", help="verify.json; a missing file means verify did not run")
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_flow)
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
