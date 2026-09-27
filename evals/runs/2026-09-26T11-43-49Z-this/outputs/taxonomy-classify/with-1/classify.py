"""Classify a product into a leaf category of taxonomy.json using typesafe.ai's Jev model.

The taxonomy has 12 top-level categories x 10 subcategories x 10 leaves = 1,200 leaf
paths, well past the 255-option cap on a single Choice question. So classification
walks the tree level by level (top-level -> subcategory -> leaf), asking one Choice
per level, and keeps the top-K highest-probability paths (beam search) since a beam
of 3 was measured to beat a greedy walk on taxonomy classification.
"""

import json
import math
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY_PATH = Path(__file__).with_name("taxonomy.json")
_BEAM_WIDTH = 3

with open(_TAXONOMY_PATH) as _f:
    _TAXONOMY: dict = json.load(_f)

_client: TypeSafeClient | None = None


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        _client = TypeSafeClient()
    return _client


def _node_at(path: list[str]) -> dict | list:
    node: dict | list = _TAXONOMY
    for step in path:
        node = node[step]
    return node


def _children(node: dict | list) -> dict[str, dict | list | None]:
    if isinstance(node, dict):
        return node
    if isinstance(node, list):
        return {leaf: None for leaf in node}
    return {}


def _option_text(name: str, subtree: dict | list | None) -> object:
    if isinstance(subtree, dict):
        return {"category": name, "includes": list(subtree.keys())}
    if isinstance(subtree, list):
        return {"category": name, "includes": subtree}
    return name


def classify(title: str, description: str) -> str:
    state = {"title": title, "description": description}
    client = _get_client()
    beams: list[tuple[list[str], float]] = [([], 0.0)]

    while True:
        expandable = [(path, lp) for path, lp in beams if _children(_node_at(path))]
        if not expandable:
            break
        next_beams: list[tuple[list[str], float]] = []
        for path, lp in expandable:
            kids = _children(_node_at(path))
            keys = {f"c{i}": name for i, name in enumerate(kids)}
            r = client.system_one(
                state=state,
                questions={
                    "next": Choice(
                        instructions=(
                            "Given the product `title` and `description`, which of "
                            "these product categories best fits this product?"
                        ),
                        criteria={
                            key: _option_text(name, kids[name])
                            for key, name in keys.items()
                        },
                    )
                },
            )
            for key, p in r.choices["next"].probabilities.items():
                if p > 0:
                    next_beams.append((path + [keys[key]], lp + math.log(p)))
        beams = sorted(
            next_beams, key=lambda b: b[1] / max(len(b[0]), 1), reverse=True
        )[:_BEAM_WIDTH]

    best_path, _ = beams[0]
    return " > ".join(best_path)
