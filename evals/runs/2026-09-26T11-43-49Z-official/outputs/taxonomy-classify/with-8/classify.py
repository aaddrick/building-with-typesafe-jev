import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

TAXONOMY_PATH = Path(__file__).with_name("taxonomy.json")
TAXONOMY = json.loads(TAXONOMY_PATH.read_text())

# Levels: top-level category (12 options) -> subcategory (10) -> leaf (10).
LEVEL_NAMES = ("top-level category", "subcategory", "leaf category")
BEAM_WIDTH = 3
EPSILON = 1e-9

client = TypeSafeClient()


def _children(path: tuple[str, ...]) -> tuple[str, ...]:
    node = TAXONOMY
    for part in path:
        node = node[part]
    return tuple(node.keys()) if isinstance(node, dict) else tuple(node)


def _choose(state: dict, level: int, labels: tuple[str, ...]) -> dict[str, float]:
    if len(labels) == 1:
        return {labels[0]: 1.0}
    keys = {f"c{i}": label for i, label in enumerate(labels)}
    question = Choice(
        instructions=(
            f"Which {LEVEL_NAMES[level]} best matches this product, "
            "based on its title and description?"
        ),
        criteria=keys,
    )
    response = client.system_one(state=state, questions={"category": question})
    probabilities = response.answers["category"].probabilities
    return {label: probabilities[key] for key, label in keys.items()}


def _extend(candidate: dict, label: str, probabilities: dict[str, float]) -> dict:
    probability_product = candidate["probability_product"] * max(
        probabilities[label], EPSILON
    )
    decision_count = candidate["decision_count"] + 1
    return {
        "path": candidate["path"] + (label,),
        "probability_product": probability_product,
        "decision_count": decision_count,
        "score": probability_product ** (1 / decision_count),
    }


def classify(title: str, description: str) -> str:
    """Return the best-matching leaf category path, e.g. "Home > Kitchen > Knives"."""
    state = {"title": title, "description": description}
    beam = [
        {"path": (), "probability_product": 1.0, "decision_count": 0, "score": 1.0}
    ]

    for level in range(len(LEVEL_NAMES)):
        with ThreadPoolExecutor(max_workers=len(beam)) as executor:
            distributions = list(
                executor.map(
                    lambda candidate: _choose(
                        state, level, _children(candidate["path"])
                    ),
                    beam,
                )
            )
        expanded = [
            _extend(candidate, label, probabilities)
            for candidate, probabilities in zip(beam, distributions)
            for label in probabilities
        ]
        beam = sorted(expanded, key=lambda c: c["score"], reverse=True)[:BEAM_WIDTH]

    best = max(beam, key=lambda c: c["score"])
    return " > ".join(best["path"])
