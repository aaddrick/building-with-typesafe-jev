"""Classify a product into a leaf category using Jev.

taxonomy.json is 12 top-level categories x 10 subcategories x 10 leaves
(1,200 leaves), which exceeds Jev's 255-option Choice cap. So we walk the
tree one level at a time (top -> sub -> leaf), each step a Choice over a
handful of options, and keep the top K partial paths (beam search) since a
single greedy path can commit to a wrong branch early.
"""

import json
import math
from functools import lru_cache
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"
BEAM_WIDTH = 3
DEPTH = 3  # top-level -> subcategory -> leaf


@lru_cache(maxsize=1)
def _taxonomy() -> dict:
    with open(TAXONOMY_PATH) as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _client() -> TypeSafeClient:
    return TypeSafeClient()


def _node_at(tree: dict, path: tuple[str, ...]):
    node = tree
    for step in path:
        node = node[step]
    return node


def _children(tree: dict, path: tuple[str, ...]) -> dict[str, str | None]:
    """Direct children of `path`, each described by what lives under it."""
    node = _node_at(tree, path)
    if isinstance(node, list):
        return {leaf: None for leaf in node}  # leaves are self-explanatory
    return {
        name: ", ".join(subtree if isinstance(subtree, list) else subtree.keys())
        for name, subtree in node.items()
    }


def classify(title: str, description: str) -> str:
    """Return the best-matching leaf category path, e.g. "Home > Kitchen > Knives"."""
    tree = _taxonomy()
    client = _client()
    state = {"title": title, "description": description}

    beams: list[tuple[tuple[str, ...], float]] = [((), 0.0)]  # (path, sum of log p)
    for _ in range(DEPTH):
        candidates: list[tuple[tuple[str, ...], float]] = []
        for path, log_p in beams:
            kids = _children(tree, path)
            keys = {f"c{i}": name for i, name in enumerate(kids)}
            r = client.system_one(
                state=state,
                questions={
                    "next": Choice(
                        instructions=(
                            "A product has the title `title` and description "
                            "`description`. Which category below is the single "
                            "best fit for it? Each option's description (when "
                            "given) lists what falls under that category."
                        ),
                        criteria={key: kids[name] for key, name in keys.items()},
                    )
                },
            )
            for key, p in r.choices["next"].probabilities.items():
                if p > 0:
                    candidates.append((path + (keys[key],), log_p + math.log(p)))
        beams = sorted(candidates, key=lambda b: b[1] / len(b[0]), reverse=True)[:BEAM_WIDTH]

    best_path, _ = beams[0]
    return " > ".join(best_path)
