"""Classify a product into a leaf category of taxonomy.json using typesafe.ai's Jev model."""

import json
import math
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"
_TAXONOMY = json.loads(_TAXONOMY_PATH.read_text())
_DEPTH = 3  # top-level -> subcategory -> leaf
_BEAM_WIDTH = 3  # beam search beat greedy 4/4 vs 2/4 on taxonomy walks (Jev cookbook)

_client: TypeSafeClient | None = None


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        _client = TypeSafeClient()
    return _client


def _children(path: list[str]) -> dict:
    """Direct children of the node at `path`, each with its own direct children as context."""
    node = _TAXONOMY
    for key in path:
        node = node[key]
    if isinstance(node, dict):
        return {
            name: (list(subtree.keys()) if isinstance(subtree, dict) else list(subtree))
            for name, subtree in node.items()
        }
    return {name: None for name in node}  # leaves: names are self-explanatory


def classify(title: str, description: str) -> str:
    """Return the taxonomy path of the best-matching leaf category, e.g. "Home > Kitchen > Knives"."""
    state = {"title": title, "description": description}
    beams: list[tuple[list[str], float]] = [([], 0.0)]  # (path so far, sum of log p)
    client = _get_client()

    for _ in range(_DEPTH):
        # One request per level: all active beams share the same state, so they
        # become separate questions in a single call instead of separate calls.
        questions = {
            f"beam_{i}": Choice(
                instructions=(
                    "Which category best matches the product described by "
                    "`title` and `description`?"
                ),
                criteria=_children(path),
            )
            for i, (path, _) in enumerate(beams)
        }
        response = client.system_one(state=state, questions=questions)

        candidates = []
        for i, (path, log_p) in enumerate(beams):
            for name, p in response.choices[f"beam_{i}"].probabilities.items():
                if p > 0:
                    candidates.append((path + [name], log_p + math.log(p)))

        beams = sorted(candidates, key=lambda b: b[1], reverse=True)[:_BEAM_WIDTH]

    best_path, _ = beams[0]
    return " > ".join(best_path)
