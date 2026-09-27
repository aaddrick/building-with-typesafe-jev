#!/usr/bin/env python3
"""The decisions behind the docs-cache, skill-coverage, and skill-reviewed workflows.

Each workflow step calls one command here, so the logic runs (and is tested
in tests/test_docs_pipeline.py) outside GitHub Actions. Commands talk to
GitHub through `gh` and write step outputs to $GITHUB_OUTPUT.

A docs copy is a workflow artifact holding llms-full.txt. A ref names one:
    {"run_id": 123, "artifact_id": 456, "sha256": "<64 hex>", "pages": 111}
Two repository variables hold refs: DOCS_LATEST (the newest copy) and
DOCS_SKILL_REVIEWED (the copy the skill was last reviewed against). Setting
them needs a token with Variables: write, passed as VARS_TOKEN; GITHUB_TOKEN
cannot. A skill-coverage pull request records the copy it covers in its
description as <!-- docs-review: REF -->.

Commands:
  compare         is a fresh fetch new, or does the cached artifact need renewing?
  record-latest   point DOCS_LATEST (and on the first run DOCS_SKILL_REVIEWED) at an upload
  plan            should skill-coverage run, and from which copy?
  use-branch      continue on the open pull request's branch
  prepare         download both copies and write the change report
  publish         open or update the pull request, or record a review that changed nothing
  record-merged   move DOCS_SKILL_REVIEWED when a skill-coverage pull request merges
"""

import argparse
import datetime as dt
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import docs_diff  # noqa: E402

REF_KEYS = ("run_id", "artifact_id", "sha256", "pages")
MARKER = re.compile(r"<!-- docs-review: (\{[^{}]*\}) -->")
BOT = ["-c", "user.name=github-actions[bot]", "-c", "user.email=github-actions[bot]@users.noreply.github.com"]
# The pull request description carries at most this much of the report.
MAX_REPORT_IN_BODY = 40_000


class PipelineError(Exception):
    pass


# Refs


def parse_ref(text: str | None) -> dict | None:
    """The ref in text, or None when it is empty or malformed."""
    if not text:
        return None
    try:
        ref = json.loads(text)
    except ValueError:
        return None
    if not isinstance(ref, dict):
        return None
    for key in ("run_id", "artifact_id", "pages"):
        if type(ref.get(key)) is not int:
            return None
    if not re.fullmatch(r"[0-9a-f]{64}", str(ref.get("sha256", ""))):
        return None
    return {k: ref[k] for k in REF_KEYS}


def dump_ref(ref: dict) -> str:
    return json.dumps(ref, separators=(",", ":"))


def marker(ref: dict) -> str:
    return f"<!-- docs-review: {dump_ref(ref)} -->"


def find_marker(body: str | None) -> dict | None:
    found = MARKER.findall(body or "")
    return parse_ref(found[-1]) if found else None


# GitHub and git


def gh(*args: str, token: str | None = None, binary: bool = False):
    env = dict(os.environ)
    if token is not None:
        env["GH_TOKEN"] = token
    result = subprocess.run(["gh", *args], capture_output=True, env=env)
    if result.returncode:
        raise PipelineError(f"gh {' '.join(args[:2])} failed: {result.stderr.decode(errors='replace').strip()}")
    return result.stdout if binary else result.stdout.decode()


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True)


def set_var(name: str, ref: dict) -> None:
    token = os.environ.get("VARS_TOKEN", "")
    if not token:
        raise PipelineError(f"The GH_PAT secret is not set, so {name} cannot be updated")
    gh("variable", "set", name, "--body", dump_ref(ref), token=token)
    print(f"{name}={dump_ref(ref)}")


def artifact_path(ref: dict) -> str:
    return f"repos/{os.environ['GITHUB_REPOSITORY']}/actions/artifacts/{ref['artifact_id']}"


def artifact_expiry(ref: dict) -> dt.datetime | None:
    """When the ref's artifact expires, or None when it is already gone."""
    try:
        info = json.loads(gh("api", artifact_path(ref)))
    except (PipelineError, ValueError):
        return None
    if info.get("expired") or not info.get("expires_at"):
        return None
    return dt.datetime.fromisoformat(info["expires_at"].replace("Z", "+00:00"))


def download(ref: dict | None, dest: Path) -> bool:
    """Write the ref's llms-full.txt to dest. False when there is no ref, the artifact is gone, or it does not match."""
    if not ref:
        return False
    try:
        blob = gh("api", f"{artifact_path(ref)}/zip", binary=True)
        with zipfile.ZipFile(io.BytesIO(blob)) as z:
            data = z.read("llms-full.txt")
    except (PipelineError, KeyError, zipfile.BadZipFile):
        return False
    if hashlib.sha256(data).hexdigest() != ref["sha256"]:
        print(f"::warning::artifact {ref['artifact_id']} does not match its sha256")
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return True


# Step outputs


def set_outputs(**values) -> None:
    lines = []
    for key, value in values.items():
        if isinstance(value, bool):
            value = "true" if value else "false"
        value = "" if value is None else str(value)
        print(f"{key}={value}")
        lines.append(f"{key}<<__OUTPUT__\n{value}\n__OUTPUT__\n")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write("".join(lines))


def step_summary(text: str) -> None:
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(text.rstrip() + "\n")


def report_head(report: str) -> str:
    """The report without its diffs: the page lists and the coverage list."""
    return report.split("\n## Diffs of changed pages")[0].rstrip() + "\n"


def now(args) -> dt.datetime:
    if getattr(args, "now", None):
        return dt.datetime.fromisoformat(args.now.replace("Z", "+00:00"))
    return dt.datetime.now(dt.timezone.utc)


# Commands


def cmd_compare(args) -> None:
    latest = parse_ref(args.latest)
    data = Path(args.fetched).read_bytes()
    text = data.decode("utf-8", errors="replace")
    # An error page or a cut-off body must never become the cached copy.
    problems = docs_diff.validate(text, latest["pages"] if latest else 0)
    if problems:
        raise PipelineError(f"the fetched docs were refused: {problems[0]}")
    sha = hashlib.sha256(data).hexdigest()
    pages = len(docs_diff.split_pages(text))

    if not latest or sha != latest["sha256"]:
        print("The docs changed." if latest else "No cached copy yet.")
        with tempfile.TemporaryDirectory() as tmp:
            previous = Path(tmp) / "previous.txt"
            if download(latest, previous):
                step_summary(report_head(docs_diff.report(
                    previous.read_text(encoding="utf-8"), text, docs_diff.skill_text(docs_diff.SKILL_DIR))))
        set_outputs(sha256=sha, pages=pages, changed=True, upload=True)
        return

    expires = artifact_expiry(latest)
    renew = expires is None or expires - now(args) < dt.timedelta(days=args.renew_days)
    print(f"Docs unchanged; artifact expires {expires or 'never: it is gone'}." + (" Renewing." if renew else ""))
    set_outputs(sha256=sha, pages=pages, changed=False, upload=renew)


def cmd_record_latest(args) -> None:
    latest = parse_ref(args.latest)
    reviewed = parse_ref(args.reviewed)
    if args.uploaded == "true":
        new = parse_ref(json.dumps({
            "run_id": args.run_id, "artifact_id": args.artifact_id, "sha256": args.sha256, "pages": args.pages,
        }))
        if not new:
            raise PipelineError("the uploaded artifact does not make a valid ref")
        set_var("DOCS_LATEST", new)
        # The first run takes the skill as reviewed against today's docs. A
        # renewed copy the skill was reviewed against moves too, so the next
        # diff still has its old side.
        if not reviewed or reviewed["sha256"] == new["sha256"]:
            set_var("DOCS_SKILL_REVIEWED", new)
            reviewed = new
        latest = new
    if not latest:
        raise PipelineError("DOCS_LATEST is not set and nothing was uploaded")
    # Stale covers a change found just now and one an earlier run found whose
    # skill update failed or has not merged. plan skips when the open pull
    # request already covers the latest copy.
    set_outputs(latest=dump_ref(latest), stale=not reviewed or reviewed["sha256"] != latest["sha256"])


def open_pr(branch: str) -> dict | None:
    prs = json.loads(gh("pr", "list", "--head", branch, "--state", "open", "--json", "number,body") or "[]")
    return prs[0] if prs else None


def cmd_plan(args) -> None:
    latest = parse_ref(args.latest)
    if not latest:
        raise PipelineError("DOCS_LATEST is not set or malformed. Run the docs cache workflow first.")
    pr = open_pr(args.branch)
    base = find_marker(pr["body"]) if pr else parse_ref(args.reviewed)
    if pr:
        print(f"Pull request #{pr['number']} covers {base['sha256'] if base else 'no recorded copy'}.")
    run = args.force == "true" or not base or base["sha256"] != latest["sha256"]
    if not run:
        print("The skill is already reviewed against the latest docs.")
    set_outputs(pr=pr["number"] if pr else "", base=dump_ref(base) if base else "", run=run)


def cmd_use_branch(args) -> None:
    git("fetch", "origin", args.branch, args.base_branch)
    git("switch", "-C", args.branch, f"origin/{args.branch}")
    git(*BOT, "merge", "--no-edit", f"origin/{args.base_branch}")


def cmd_prepare(args) -> None:
    if not download(parse_ref(args.latest), Path(args.docs)):
        raise PipelineError("The latest docs artifact is gone. Run the docs cache workflow to renew it.")
    old = ""
    with tempfile.TemporaryDirectory() as tmp:
        previous = Path(tmp) / "old.txt"
        if download(parse_ref(args.base), previous):
            old = previous.read_text(encoding="utf-8")
        else:
            # A reviewed copy whose artifact expired leaves no old side, so
            # every page reads as added and Claude reviews the lot.
            print("::warning::No reviewed copy to diff against; every page reads as added.")
    report = docs_diff.report(old, Path(args.docs).read_text(encoding="utf-8"), docs_diff.skill_text(Path(args.skill)))
    Path(args.report).write_text(report, encoding="utf-8")
    step_summary(report_head(report))


def cmd_publish(args) -> None:
    latest = parse_ref(args.latest)
    if not latest:
        raise PipelineError("no valid latest ref to publish against")
    date = now(args).date().isoformat()
    review = (
        Path(args.summary).read_text(encoding="utf-8").strip()
        + "\n\n<details><summary>Docs change report</summary>\n\n"
        + report_head(Path(args.report).read_text(encoding="utf-8"))[:MAX_REPORT_IN_BODY]
        + "\n</details>\n"
    )
    footer = f"🤖 Generated with [Claude Code](https://claude.com/claude-code) by [skill-coverage]({args.run_url})"

    git("add", "-A", args.skill)
    edited = subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode != 0
    if edited:
        git(*BOT, "commit", "-m", f"Update the skill for the TypeSafe docs of {date}",
            "-m", "Generated by .github/workflows/skill-coverage.yml.")

    with tempfile.TemporaryDirectory() as tmp:
        body_file = Path(tmp) / "body.md"
        if args.pr:
            # The branch now covers the latest copy, edits or not.
            if edited:
                git("push", "origin", f"HEAD:{args.branch}")
            body = json.loads(gh("pr", "view", args.pr, "--json", "body"))["body"]
            body_file.write_text(MARKER.sub("", body).rstrip() + "\n\n" + marker(latest) + "\n", encoding="utf-8")
            gh("pr", "edit", args.pr, "--body-file", str(body_file))
            news = "Pushed more edits." if edited else "No further edits needed."
            body_file.write_text(f"The docs changed again on {date}. {news}\n\n{review}\n{footer}\n", encoding="utf-8")
            gh("pr", "comment", args.pr, "--body-file", str(body_file))
            set_outputs(outcome="updated")
            return

        if not edited:
            print("No skill edits needed; recording the review.")
            set_var("DOCS_SKILL_REVIEWED", latest)
            set_outputs(outcome="recorded")
            return

        # No pull request is open, so any leftover branch is merged or
        # abandoned and a fresh one replaces it.
        git("push", "--force", "origin", f"HEAD:{args.branch}")
        body_file.write_text(
            f"{review}\nMerging records the skill as reviewed against this copy of the docs "
            "(DOCS_SKILL_REVIEWED). Closing without merging leaves it, so the next run reviews "
            f"these changes again.\n\n{footer}\n\n{marker(latest)}\n",
            encoding="utf-8",
        )
        gh("pr", "create", "--base", args.base_branch, "--head", args.branch,
           "--title", f"Update the skill for the TypeSafe docs of {date}", "--body-file", str(body_file))
        set_outputs(outcome="opened")


def cmd_record_merged(args) -> None:
    # The description is editable, so only a well-formed ref counts.
    ref = find_marker(os.environ.get("PR_BODY", ""))
    if not ref:
        raise PipelineError("No valid docs-review marker in the pull request description")
    current = parse_ref(args.reviewed)
    # Never move backward: an older pull request merged late must not undo
    # a newer recorded review.
    if current and ref["run_id"] < current["run_id"]:
        print("DOCS_SKILL_REVIEWED already names a newer copy; leaving it.")
        return
    set_var("DOCS_SKILL_REVIEWED", ref)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("compare")
    p.add_argument("--fetched", required=True)
    p.add_argument("--latest", default="")
    p.add_argument("--renew-days", type=int, default=14)
    p.add_argument("--now", help="ISO time to treat as now (tests)")
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("record-latest")
    p.add_argument("--latest", default="")
    p.add_argument("--reviewed", default="")
    p.add_argument("--uploaded", choices=["true", "false"], required=True)
    p.add_argument("--run-id", type=lambda v: int(v) if v else None)
    p.add_argument("--artifact-id", type=lambda v: int(v) if v else None)
    p.add_argument("--sha256", default="")
    p.add_argument("--pages", type=lambda v: int(v) if v else None)
    p.set_defaults(func=cmd_record_latest)

    p = sub.add_parser("plan")
    p.add_argument("--latest", default="")
    p.add_argument("--reviewed", default="")
    p.add_argument("--branch", required=True)
    p.add_argument("--force", default="false")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("use-branch")
    p.add_argument("--branch", required=True)
    p.add_argument("--base-branch", required=True)
    p.set_defaults(func=cmd_use_branch)

    p = sub.add_parser("prepare")
    p.add_argument("--latest", default="")
    p.add_argument("--base", default="")
    p.add_argument("--docs", required=True, help="where Claude reads the latest copy")
    p.add_argument("--report", required=True)
    p.add_argument("--skill", default=str(docs_diff.SKILL_DIR))
    p.set_defaults(func=cmd_prepare)

    p = sub.add_parser("publish")
    p.add_argument("--latest", default="")
    p.add_argument("--pr", default="")
    p.add_argument("--branch", required=True)
    p.add_argument("--base-branch", required=True)
    p.add_argument("--skill", required=True)
    p.add_argument("--summary", required=True)
    p.add_argument("--report", required=True)
    p.add_argument("--run-url", default="")
    p.add_argument("--now", help="ISO time to treat as now (tests)")
    p.set_defaults(func=cmd_publish)

    p = sub.add_parser("record-merged", help="reads the pull request description from PR_BODY")
    p.add_argument("--reviewed", default="")
    p.set_defaults(func=cmd_record_merged)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (PipelineError, subprocess.CalledProcessError) as exc:
        print(f"::error::{exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
