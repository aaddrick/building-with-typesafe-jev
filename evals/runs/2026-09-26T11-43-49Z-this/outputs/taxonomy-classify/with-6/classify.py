"""Classify a product into a leaf category of taxonomy.json using Jev."""

import json
import math
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"
_BEAM_WIDTH = 3

with open(_TAXONOMY_PATH) as _f:
    _TAXONOMY: dict = json.load(_f)

# One client, reused across calls (per SDK guidance: don't create a client per request).
_client = TypeSafeClient()


def _node_at(path: list[str]):
    node = _TAXONOMY
    for name in path:
        node = node[name]
    return node


def _children(node) -> dict[str, object]:
    """Direct children of a taxonomy node, keyed by name, valued by their subtree (or None for a leaf)."""
    if isinstance(node, dict):
        return node
    if isinstance(node, list):
        return {name: None for name in node}
    return {}


def _describe(subtree) -> str | None:
    """Short blurb of what lives under a child, shown as its Choice option so the model can see the subtree."""
    if isinstance(subtree, dict):
        return f"Subcategories: {', '.join(subtree.keys())}"
    if isinstance(subtree, list):
        return f"Includes: {', '.join(subtree)}"
    return None


def classify(title: str, description: str) -> str:
    """Return the best-matching leaf category path, e.g. "Home > Kitchen > Knives"."""
    state = {"title": title, "description": description}

    # Geometric mean of edge probabilities so shallow and deep paths compare fairly.
    def path_score(beam: tuple[list[str], float, int]) -> float:
        _, log_p, decisions = beam
        return math.exp(log_p / decisions) if decisions else 1.0

    # Beam of (path so far, sum of log-probabilities, number of real decisions made).
    beams: list[tuple[list[str], float, int]] = [([], 0.0, 0)]

    while True:
        expandable = []
        finished = []
        for path, log_p, decisions in beams:
            kids = _children(_node_at(path))
            if kids:
                expandable.append((path, log_p, decisions, kids))
            else:
                finished.append((path, log_p, decisions))

        if not expandable:
            beams = finished
            break

        questions = {
            f"path_{i}": Choice(
                instructions=(
                    "A product with the given `title` and `description` is being filed into a category "
                    f"tree. It is already under {' > '.join(path) or 'the top level'}. "
                    "Which direct subcategory best matches it?"
                ),
                criteria={name: _describe(sub) for name, sub in kids.items()},
            )
            for i, (path, log_p, decisions, kids) in enumerate(expandable)
        }
        r = _client.system_one(state=state, questions=questions)

        next_beams = list(finished)
        for i, (path, log_p, decisions, kids) in enumerate(expandable):
            probabilities = r.choices[f"path_{i}"].probabilities
            multi_option = len(probabilities) > 1
            for name, p in probabilities.items():
                if p <= 0:
                    continue
                next_beams.append((
                    path + [name],
                    log_p + math.log(p),
                    decisions + (1 if multi_option else 0),
                ))

        beams = sorted(next_beams, key=path_score, reverse=True)[:_BEAM_WIDTH]

    best_path, _, _ = max(beams, key=path_score)
    return " > ".join(best_path)
