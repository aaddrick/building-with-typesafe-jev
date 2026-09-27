"""Classify products into taxonomy.json leaf categories using typesafe.ai's Jev model."""

import json
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"
_BEAM_WIDTH = 3
_EPSILON = 1e-9

with open(_TAXONOMY_PATH) as f:
    _TAXONOMY: dict[str, dict[str, list[str]]] = json.load(f)

_client = TypeSafeClient()


def _query_choice(state: str, options: list[str]) -> dict[str, float]:
    if len(options) == 1:
        return {options[0]: 1.0}

    # Use synthetic keys since option labels (e.g. "Men's Tops") aren't valid criteria keys.
    key_map = {f"opt_{i}": label for i, label in enumerate(options)}
    response = _client.system_one(
        state=state,
        questions={
            "category": Choice(
                instructions="Which product category best matches this product?",
                criteria=key_map,
            ),
        },
    )
    probs = response.answers["category"].probabilities
    return {label: probs[key] for key, label in key_map.items()}


def classify(title: str, description: str) -> str:
    """Return the best-matching leaf category path, e.g. 'Home > Kitchen > Knives'."""
    state = f"Title: {title}\nDescription: {description}"

    top_probs = _query_choice(state, list(_TAXONOMY))
    beam = [((top,), prob) for top, prob in top_probs.items()]
    beam = sorted(beam, key=lambda c: c[1], reverse=True)[:_BEAM_WIDTH]

    for depth in range(2):
        candidates = []
        for path, score in beam:
            if depth == 0:
                options = list(_TAXONOMY[path[0]])
            else:
                options = _TAXONOMY[path[0]][path[1]]
            probs = _query_choice(state, options)
            for label, prob in probs.items():
                candidates.append((path + (label,), score * max(prob, _EPSILON)))
        beam = sorted(candidates, key=lambda c: c[1], reverse=True)[:_BEAM_WIDTH]

    best_path, _ = max(beam, key=lambda c: c[1])
    return " > ".join(best_path)
