"""Classify products into the taxonomy in taxonomy.json using typesafe.ai's Jev model.

The taxonomy is 12 top-level categories x 10 subcategories x 10 leaves = 1,200
leaves, well past Jev's 255-option Choice cap, so classification walks the tree
one level at a time (top -> sub -> leaf), keeping the top-K beams at each level
per the taxonomy-walk pattern in typesafe.ai's prior art.
"""

import json
import math
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY_PATH = Path(__file__).with_name("taxonomy.json")
_BEAM_WIDTH = 3

_client: TypeSafeClient | None = None


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        _client = TypeSafeClient()
    return _client


def _load_taxonomy() -> dict:
    with open(_TAXONOMY_PATH) as f:
        return json.load(f)


def _children(taxonomy: dict, path: tuple[str, ...]) -> dict[str, str | None]:
    """Names -> description of what's under them, for the node at `path`."""
    if len(path) == 0:
        return {top: ", ".join(subs.keys()) for top, subs in taxonomy.items()}
    if len(path) == 1:
        subs = taxonomy[path[0]]
        return {sub: ", ".join(leaves) for sub, leaves in subs.items()}
    if len(path) == 2:
        leaves = taxonomy[path[0]][path[1]]
        return {leaf: None for leaf in leaves}
    return {}


_LEVEL_LABEL = ("top-level category", "subcategory", "specific leaf category")


def classify(title: str, description: str) -> str:
    """Return the best-matching leaf category path, e.g. "Home > Kitchen > Knives"."""
    taxonomy = _load_taxonomy()
    client = _get_client()
    state = {"title": title, "description": description}

    beams: list[tuple[tuple[str, ...], float]] = [((), 0.0)]
    depth = 0
    while any(_children(taxonomy, path) for path, _ in beams):
        label = _LEVEL_LABEL[depth]
        next_beams: list[tuple[tuple[str, ...], float]] = []
        for path, log_p in beams:
            kids = _children(taxonomy, path)
            if not kids:
                next_beams.append((path, log_p))
                continue

            keys = {f"c{i}": name for i, name in enumerate(kids)}
            criteria = {
                key: (name if desc is None else f"{name} (includes: {desc})")
                for key, name in keys.items()
                for desc in [kids[name]]
            }
            r = client.system_one(
                state=state,
                questions={
                    "next": Choice(
                        instructions=(
                            f"Which {label} best fits this product, based on "
                            "`title` and `description`?"
                        ),
                        criteria=criteria,
                    )
                },
            )
            for key, p in r.choices["next"].probabilities.items():
                if p > 0:
                    next_beams.append((path + (keys[key],), log_p + math.log(p)))

        beams = sorted(
            next_beams, key=lambda b: b[1] / max(len(b[0]), 1), reverse=True
        )[:_BEAM_WIDTH]
        depth += 1

    best_path, _ = beams[0]
    return " > ".join(best_path)
