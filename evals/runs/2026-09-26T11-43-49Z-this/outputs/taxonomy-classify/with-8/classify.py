"""Classify a product into a leaf category of taxonomy.json using Jev.

taxonomy.json is a fixed 3-level tree (12 top categories, 10 subcategories each,
10 leaves each) -- too many leaves (1,200) for a single Choice (255-option cap),
so this walks the tree one Choice per level with beam search (K=3), which the
Jev docs report beats greedy on taxonomy walks (4/4 vs 2/4 correct).
"""

import json
import math
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"
_BEAM_WIDTH = 3
_LEVEL_LABELS = ["top-level product category", "subcategory", "specific leaf category"]

_client: TypeSafeClient | None = None


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        _client = TypeSafeClient()
    return _client


def _load_taxonomy() -> dict:
    with open(_TAXONOMY_PATH) as f:
        return json.load(f)


def _get_node(taxonomy: dict, path: list[str]):
    node = taxonomy
    for key in path:
        node = node[key]
    return node


def classify(title: str, description: str) -> str:
    taxonomy = _load_taxonomy()
    client = _get_client()
    state = {"title": title, "description": description}

    beams: list[tuple[list[str], float]] = [([], 0.0)]  # (path, sum of log p)
    for depth in range(3):
        next_beams: list[tuple[list[str], float]] = []
        for path, log_prob in beams:
            node = _get_node(taxonomy, path)
            if depth < 2:
                # Show each child's own children so the model can see what lives
                # under that branch, not just its name.
                criteria = {
                    name: ", ".join(child if depth == 1 else child.keys())
                    for name, child in node.items()
                }
            else:
                criteria = {name: None for name in node}  # leaves are self-explanatory

            where = f" under `{' > '.join(path)}`" if path else ""
            response = client.system_one(
                state=state,
                questions={
                    "next": Choice(
                        instructions=(
                            f"Given `title` and `description`, which {_LEVEL_LABELS[depth]}"
                            f"{where} best fits this product?"
                        ),
                        criteria=criteria,
                    )
                },
            )
            for name, p in response.choices["next"].probabilities.items():
                if p > 0:
                    next_beams.append((path + [name], log_prob + math.log(p)))

        beams = sorted(next_beams, key=lambda b: b[1] / len(b[0]), reverse=True)[:_BEAM_WIDTH]

    best_path, _ = beams[0]
    return " > ".join(best_path)
