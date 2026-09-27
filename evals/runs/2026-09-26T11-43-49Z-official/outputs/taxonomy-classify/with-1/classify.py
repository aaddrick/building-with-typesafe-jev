"""Classify a product into a leaf category of taxonomy.json using TypeSafe's Jev model."""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY: dict = json.loads((Path(__file__).parent / "taxonomy.json").read_text())

_BEAM_WIDTH = 3
_LEVEL_INSTRUCTIONS = (
    "Which top-level product category does this product belong to?",
    "Which subcategory of the chosen top-level category best fits this product?",
    "Which specific product type best fits this product?",
)

_client = TypeSafeClient(model="jev-latest")


def _children(path: tuple[str, ...]) -> tuple[str, ...]:
    node = _TAXONOMY
    for label in path:
        node = node[label]
    return tuple(node)


def _ask(state: dict[str, str], labels: tuple[str, ...], instructions: str) -> dict[str, float]:
    question = Choice(instructions=instructions, criteria={label: None for label in labels})
    response = _client.system_one(state=state, questions={"category": question})
    return response.choices["category"].probabilities


def classify(title: str, description: str) -> str:
    """Return the taxonomy.json path of the best-matching leaf category, e.g. "Home > Kitchen > Knives"."""
    state = {"title": title, "description": description}
    beam: list[tuple[tuple[str, ...], float]] = [((), 1.0)]

    for instructions in _LEVEL_INSTRUCTIONS:
        with ThreadPoolExecutor(max_workers=len(beam)) as executor:
            distributions = executor.map(
                lambda candidate: _ask(state, _children(candidate[0]), instructions), beam
            )
        expanded = [
            (path + (label,), score * probability)
            for (path, score), probabilities in zip(beam, distributions)
            for label, probability in probabilities.items()
        ]
        beam = sorted(expanded, key=lambda candidate: candidate[1], reverse=True)[:_BEAM_WIDTH]

    best_path, _ = beam[0]
    return " > ".join(best_path)
