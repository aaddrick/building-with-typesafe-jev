"""Every question Jev is asked in the docs pipeline, and every threshold its answers meet.

This is the file to review and tune (rule 11 of the skill). scripts/jev_triage.py
builds the state, asks, and routes; it holds no wording and no numbers of its own.

Two moments call Jev:
- triage, before Claude: one request per changed or added docs page decides
  whether Claude needs to see it at all, and which skill file it touches.
- verify, after Claude: one request per page Claude was sent checks that the
  edited skill file now agrees with the docs.
"""

# Pinned, not jev-latest: the thresholds below were set against this version,
# and an alias moves on a new release. The JEV_MODEL variable overrides it.
MODEL = "jev-1.13.0"

# Each text field in a state is cut to this many characters, which keeps state
# plus the longest question well under the 32k-token limit.
MAX_STATE_CHARS = 12_000
# Lines of unchanged context kept around each change in a page.
CONTEXT_LINES = 2

# Triage bands. A changed page is skipped only when Jev is this sure it is
# wording or example-only and a coding agent would write the same code.
SKIP_KIND_CONFIDENCE = 0.80
SKIP_MAX_MISLEADS = 0.5
# Below this, the kind is a guess: Claude sees the page and decides.
UNSURE_KIND_CONFIDENCE = 0.50
# "No skill file" is trusted to skip a page only this confidently.
SKIP_TARGET_CONFIDENCE = 0.80
# An added page goes to Claude at or above this P(worth), is skipped at or
# below the second, and is left to Claude to judge in between.
ADD_WORTH = 0.70
SKIP_WORTH = 0.30

# Verify bands. An edited page passes when a conflict is this unlikely and,
# for a changed fact, the new form is this likely present.
MAX_CONFLICT = 0.30
MIN_COVERED = 0.60

SKILL_FILES = {
    "SKILL.md": {
        "what": "The design rules for building with Jev: picking a primitive, writing questions, structuring state, and using probabilities and confidence",
        "not_for": "Exact field names, SDK signatures, limits, prices, or worked examples",
    },
    "api-reference.md": {
        "what": "Exact request and response shapes, SDK classes and signatures, errors, limits, models, and prices",
        "not_for": "Design advice or architectures",
    },
    "patterns.md": {
        "what": "Architectures and techniques from the official pattern pages and cookbooks, with their starting thresholds",
        "not_for": "API details or general design rules",
    },
    "none": {
        "what": "Nothing a coding agent needs to build with Jev: company, legal, navigation, marketing, or install steps for other tools",
        "not_for": "Anything about calling Jev or designing with it",
    },
}

KIND = {
    "type": "choice",
    "instructions": "What kind of change turns `change.before` into `change.after` on the docs page `page.title`?",
    "criteria": {
        "wording": {
            "what": "The same facts in other words: rephrasing, formatting, typo fixes, reordered sentences, changed links or images",
            "not_for": "Any name, number, default, limit, or behavior that differs",
        },
        "example_only": {
            "what": "Only a code sample, walkthrough, or sample data changed, and the API and advice it shows are the same",
            "not_for": "A sample that now uses a different name, parameter, or behavior",
        },
        "api_fact": {
            "what": "A field, parameter, request or response shape, SDK signature, error, limit, default, model name, or price differs",
            "not_for": "The same fact reworded",
        },
        "new_capability": {
            "what": "`change.after` documents something Jev or its SDKs can do that `change.before` does not: a new primitive, endpoint, method, option, or model",
            "not_for": "A fact that was already there and changed value",
        },
        "guidance": {
            "what": "Advice changed: a recommended threshold, pattern, practice, or known weakness",
            "not_for": "API facts",
        },
        "other": {
            "what": "None of the other kinds fits",
            "not_for": "A change that one of the other kinds describes",
        },
    },
}

MISLEADS = {
    "type": "score",
    "instructions": "A coding agent writes code with Jev from the old text `change.before` instead of the new text `change.after`. What happens to its code?",
    "criteria": [
        "The code is the same either way",
        "The code works, but misses a newer option or recommendation",
        "The code breaks or behaves wrongly: a wrong name, shape, limit, default, or price",
    ],
}

TARGET = {
    "type": "choice",
    "instructions": "If this docs change matters to a coding agent, which file of a skill that teaches building with Jev would state it?",
    "criteria": SKILL_FILES,
}

WORTH = {
    "type": "noul",
    "instructions": "Does `page.text` teach a coding agent something about calling Jev or designing with it?",
    "criteria": {
        "true": "It states an API fact, SDK usage, a technique, a pattern, or a known weakness",
        "false": "It is company, legal, navigation, marketing, or tool-install content",
    },
}

CONFLICT = {
    "type": "noul",
    "instructions": "Does `skill.text` state something that `docs.after` contradicts on the same point?",
    "criteria": {
        "true": "`skill.text` gives a different name, number, default, limit, shape, or behavior than `docs.after` for the same thing",
        "false": "`skill.text` agrees with `docs.after`, or does not cover the point",
    },
}

COVERED = {
    "type": "noul",
    "instructions": "Does `skill.text` state what changed between `docs.before` and `docs.after`, in its form from `docs.after`?",
    "criteria": {
        "true": "`skill.text` states the new name, value, capability, or advice",
        "false": "`skill.text` states only the old form, or leaves it out",
    },
}

CHANGED_PAGE_QUESTIONS = {"kind": KIND, "misleads": MISLEADS, "target": TARGET}
ADDED_PAGE_QUESTIONS = {"worth": WORTH, "target": TARGET}
VERIFY_QUESTIONS = {"conflict": CONFLICT, "covered": COVERED}
