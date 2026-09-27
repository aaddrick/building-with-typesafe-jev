"""Classify a product into a leaf category of taxonomy.json using typesafe.ai's Jev model.

Walks the fixed 3-level tree (top-level > subcategory > leaf) with a Choice
question per level, using beam search so an ambiguous early pick can be
corrected by clearer evidence further down (a single greedy walk cannot
recover from a bad first guess).
"""

import json
import math
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

MODEL = "jev-1.13.0"
BEAM_WIDTH = 3
TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"

_taxonomy: dict | None = None
_client: TypeSafeClient | None = None


def _get_taxonomy() -> dict:
    global _taxonomy
    if _taxonomy is None:
        _taxonomy = json.loads(TAXONOMY_PATH.read_text())
    return _taxonomy


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        _client = TypeSafeClient(model=MODEL)
    return _client


def _node_at(taxonomy: dict, path: list[str]):
    node = taxonomy
    for name in path:
        node = node[name]
    return node


def _options(taxonomy: dict, path: list[str]) -> dict[str, str | None]:
    """Direct children of `path`, described by a preview of what's under each."""
    node = _node_at(taxonomy, path)
    if isinstance(node, dict):
        return {
            name: ", ".join(child if isinstance(child, list) else child.keys())
            for name, child in node.items()
        }
    return {name: None for name in node}  # leaf level: names are self-explanatory


def classify(title: str, description: str) -> str:
    taxonomy = _get_taxonomy()
    client = _get_client()
    state = {"title": title, "description": description}

    beams: list[tuple[list[str], float]] = [([], 0.0)]
    for _ in range(3):  # top-level, subcategory, leaf
        candidates: list[tuple[list[str], float]] = []
        for path, log_p in beams:
            options = _options(taxonomy, path)
            keys = {f"c{i}": name for i, name in enumerate(options)}
            r = client.system_one(
                state=state,
                questions={
                    "next": Choice(
                        instructions=(
                            "Given the product `title` and `description`, which of "
                            "these categories best fits the product?"
                        ),
                        criteria={key: options[name] for key, name in keys.items()},
                    )
                },
            )
            for key, p in r.choices["next"].probabilities.items():
                if p > 0:
                    candidates.append((path + [keys[key]], log_p + math.log(p)))
        beams = sorted(candidates, key=lambda b: b[1] / len(b[0]), reverse=True)[:BEAM_WIDTH]

    best_path, _ = beams[0]
    return " > ".join(best_path)
