import json
import math
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"
_MODEL = "jev-latest"
_BEAM_WIDTH = 3

with open(_TAXONOMY_PATH) as _f:
    _TAXONOMY = json.load(_f)


def _path_score(probs: list[float]) -> float:
    return math.prod(probs) ** (1 / len(probs))


def _expand(beam: list[tuple[list[str], list[float]]], answers: dict) -> list[tuple[list[str], list[float]]]:
    expanded = []
    for i, (path, probs) in enumerate(beam):
        answer = answers[f"q{i}"]
        for label, prob in answer.probabilities.items():
            if prob > 0:
                expanded.append((path + [label], probs + [prob]))
    expanded.sort(key=lambda p: -_path_score(p[1]))
    return expanded[:_BEAM_WIDTH]


def classify(title: str, description: str) -> str:
    """Return the best-matching leaf category path, e.g. "Home > Kitchen > Knives"."""
    state = {"title": title, "description": description}

    with TypeSafeClient() as client:
        top_labels = list(_TAXONOMY.keys())
        response = client.system_one(
            state=state,
            model=_MODEL,
            questions={
                "q0": Choice(
                    instructions="Which top-level product category best fits this product?",
                    criteria={label: None for label in top_labels},
                ),
            },
        )
        top_probs = sorted(response.choices["q0"].probabilities.items(), key=lambda kv: -kv[1])
        beam = [([label], [prob]) for label, prob in top_probs[:_BEAM_WIDTH] if prob > 0]

        sub_questions = {
            f"q{i}": Choice(
                instructions=f"Which subcategory of '{path[0]}' best fits this product?",
                criteria={label: None for label in _TAXONOMY[path[0]]},
            )
            for i, (path, _probs) in enumerate(beam)
        }
        response = client.system_one(state=state, model=_MODEL, questions=sub_questions)
        beam = _expand(beam, response.choices)

        leaf_questions = {
            f"q{i}": Choice(
                instructions=f"Which specific product type under '{path[0]} > {path[1]}' best fits this product?",
                criteria={label: None for label in _TAXONOMY[path[0]][path[1]]},
            )
            for i, (path, _probs) in enumerate(beam)
        }
        response = client.system_one(state=state, model=_MODEL, questions=leaf_questions)
        beam = _expand(beam, response.choices)

    return " > ".join(beam[0][0])
