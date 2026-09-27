#!/usr/bin/env python3
"""Compare two copies of docs.typesafe.ai/llms-full.txt, page by page.

llms-full.txt is every docs page joined together, each opening with
`# Title` and `Source: https://docs.typesafe.ai/<slug>`. The docs-cache
workflow uses this script twice:

- `validate NEW --against OLD` refuses a fetch that is not the docs (an error
  page, a truncated body) before it can replace the cache.
- `report --old OLD --new NEW` writes the Markdown the skill-coverage
  workflow hands to Claude and puts in the pull request: which pages were
  added, removed, or changed, their diffs, and which pages the skill never
  names.
"""

import argparse
import difflib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "building-with-typesafe-jev"
PAGE_HEAD = re.compile(r"^# (.+)\nSource: https://docs\.typesafe\.ai/(\S*)$", re.M)
# A changed page's diff past this many lines is cut; the full page is in the cache.
MAX_DIFF_LINES = 300
# Past this many characters the report stops inlining diffs, so the prompt stays bounded.
MAX_REPORT_CHARS = 200_000


def split_pages(text: str) -> dict[str, tuple[str, str]]:
    """Map each page's slug to (title, body). The body includes its header."""
    heads = list(PAGE_HEAD.finditer(text))
    pages = {}
    for i, head in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        pages[head.group(2).rstrip("/")] = (head.group(1).strip(), text[head.start():end].rstrip() + "\n")
    return pages


def referenced(slug: str, skill_text: str) -> bool:
    """True when the skill names this page by URL, by backticked path, or, for a cookbook, by its bare slug."""
    s = re.escape(slug)
    if re.search(rf"docs\.typesafe\.ai/{s}(?:\.md)?(?![\w/-])", skill_text):
        return True
    if re.search(rf"`{s}(?:\.md)?`", skill_text):
        return True
    if slug.startswith("cookbooks/"):
        return f"`{slug.split('/', 1)[1]}`" in skill_text
    return False


def skill_text(skill_dir: Path) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in sorted(skill_dir.rglob("*.md")))


def fence(body: str) -> str:
    """A backtick fence longer than any run of backticks inside the body."""
    longest = max((len(m) for m in re.findall(r"`+", body)), default=0)
    return "`" * max(3, longest + 1)


def report(old_text: str, new_text: str, skill: str) -> str:
    old, new = split_pages(old_text), split_pages(new_text)
    added = sorted(new.keys() - old.keys())
    removed = sorted(old.keys() - new.keys())
    changed = sorted(s for s in new.keys() & old.keys() if new[s][1] != old[s][1])
    unreferenced = [s for s in sorted(new) if not referenced(s, skill)]

    out = [
        "# TypeSafe docs change report",
        "",
        f"{len(old)} pages before, {len(new)} after: "
        f"{len(added)} added, {len(removed)} removed, {len(changed)} changed.",
        "",
    ]

    def listing(title: str, slugs: list[str], pages: dict) -> None:
        out.append(f"## {title} ({len(slugs)})")
        out.append("")
        out.extend(f"- `{s}`: {pages[s][0]}" for s in slugs)
        if not slugs:
            out.append("None.")
        out.append("")

    listing("Added pages", added, new)
    listing("Removed pages", removed, old)
    listing("Changed pages", changed, new)

    out.append(f"## Pages the skill does not name ({len(unreferenced)} of {len(new)})")
    out.append("")
    out.append("Not every page needs a link. Generated SDK reference pages are usually covered by `api-reference.md`.")
    out.append("")
    out.extend(f"- `{s}`{' (new)' if s in added else ''}: {new[s][0]}" for s in unreferenced)
    out.append("")

    out.append("## Diffs of changed pages")
    out.append("")
    out.append("Added pages are not inlined. Read them in `upstream/typesafe-docs/llms-full.txt`.")
    out.append("")
    size = sum(len(line) + 1 for line in out)
    for slug in changed:
        diff = list(difflib.unified_diff(
            old[slug][1].splitlines(), new[slug][1].splitlines(),
            fromfile=f"old/{slug}", tofile=f"new/{slug}", lineterm="", n=2,
        ))
        cut = len(diff) - MAX_DIFF_LINES
        body = "\n".join(diff[:MAX_DIFF_LINES])
        if cut > 0:
            body += f"\n... {cut} more diff lines cut"
        block = f"### `{slug}`\n\n{fence(body)}diff\n{body}\n{fence(body)}\n"
        if size + len(block) > MAX_REPORT_CHARS:
            out.append(f"### `{slug}`\n\nDiff left out to keep the report bounded. Compare the page in the cache.\n")
            continue
        out.append(block)
        size += len(block)
    return "\n".join(out).rstrip() + "\n"


def validate(new_text: str, old_text: str) -> list[str]:
    """Reasons to refuse a fetch. Empty means it looks like the docs."""
    new, old = split_pages(new_text), split_pages(old_text)
    if not new:
        return ["no `# Title` / `Source: https://docs.typesafe.ai/...` page headers"]
    if len(new) * 2 < len(old):
        return [f"only {len(new)} pages, down from {len(old)}; looks truncated"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    rep = sub.add_parser("report", help="Markdown report of what changed and what the skill does not name")
    rep.add_argument("--old", type=Path, required=True, help="previous llms-full.txt (a missing or empty file means none)")
    rep.add_argument("--new", type=Path, required=True)
    rep.add_argument("--skill", type=Path, default=SKILL_DIR)
    val = sub.add_parser("validate", help="exit 1 if a fetch does not look like the docs")
    val.add_argument("new", type=Path)
    val.add_argument("--against", type=Path, help="the cached copy it would replace")
    args = parser.parse_args()

    def read(path: Path | None) -> str:
        return path.read_text(encoding="utf-8") if path and path.is_file() else ""

    if args.cmd == "report":
        sys.stdout.write(report(read(args.old), read(args.new), skill_text(args.skill)))
        return 0
    problems = validate(read(args.new), read(args.against))
    for p in problems:
        print(f"error: {args.new}: {p}", file=sys.stderr)
    if not problems:
        print(f"ok: {len(split_pages(read(args.new)))} pages")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
