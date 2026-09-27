#!/usr/bin/env python3
"""A stand-in for the `gh` CLI, backed by a JSON file named in FAKE_GH_STATE.

It answers only the calls scripts/docs_pipeline.py makes: repository
variables, workflow artifacts, and pull requests. Every call is recorded in
state["calls"]. Anything else exits 1, so a new call fails its test loudly.
"""

import io
import json
import os
import re
import sys
import zipfile

path = os.environ["FAKE_GH_STATE"]
with open(path, encoding="utf-8") as f:
    state = json.load(f)
args = sys.argv[1:]
state["calls"].append(args)


def save():
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f)


def fail(message):
    save()
    sys.stderr.write(message + "\n")
    sys.exit(1)


def opt(name):
    return args[args.index(name) + 1]


if args[:2] == ["variable", "set"]:
    if not os.environ.get("GH_TOKEN"):
        fail("HTTP 401: no token")
    state["vars"][args[2]] = opt("--body")
elif args[:1] == ["api"]:
    m = re.fullmatch(r"repos/[^/]+/[^/]+/actions/artifacts/(\d+)(/zip)?", args[1])
    artifact = state["artifacts"].get(m.group(1)) if m else None
    if not artifact:
        fail("HTTP 404: Not Found")
    if m.group(2):
        if artifact["expired"]:
            fail("HTTP 410: Gone")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("llms-full.txt", artifact["content"])
        save()
        sys.stdout.buffer.write(buf.getvalue())
        sys.exit(0)
    print(json.dumps({"id": int(m.group(1)), "expired": artifact["expired"], "expires_at": artifact["expires_at"]}))
elif args[:2] == ["pr", "list"]:
    head = opt("--head")
    print(json.dumps([
        {"number": int(n), "body": pr["body"]}
        for n, pr in state["prs"].items() if pr["state"] == "open" and pr["head"] == head
    ]))
elif args[:2] == ["pr", "view"]:
    print(json.dumps({"body": state["prs"][args[2]]["body"]}))
elif args[:2] == ["pr", "edit"]:
    state["prs"][args[2]]["body"] = open(opt("--body-file"), encoding="utf-8").read()
elif args[:2] == ["pr", "comment"]:
    state["prs"][args[2]]["comments"].append(open(opt("--body-file"), encoding="utf-8").read())
elif args[:2] == ["pr", "create"]:
    number = str(len(state["prs"]) + 1)
    state["prs"][number] = {
        "head": opt("--head"), "base": opt("--base"), "title": opt("--title"),
        "body": open(opt("--body-file"), encoding="utf-8").read(), "state": "open", "comments": [],
    }
    print(f"https://github.com/o/r/pull/{number}")
else:
    fail(f"fake gh does not handle: {args}")
save()
