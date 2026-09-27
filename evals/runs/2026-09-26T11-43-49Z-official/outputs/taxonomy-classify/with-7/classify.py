import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

MODEL = "jev-latest"
BEAM_WIDTH = 3

TAXONOMY: dict = json.loads((Path(__file__).parent / "taxonomy.json").read_text())

client = TypeSafeClient()


def _node_at(path: tuple[str, ...]):
    node = TAXONOMY
    for label in path:
        node = node[label]
    return node


def _options_at(path: tuple[str, ...]) -> list[str]:
    node = _node_at(path)
    return list(node.keys()) if isinstance(node, dict) else list(node)


def _instructions_for(path: tuple[str, ...]) -> str:
    if not path:
        return "Which top-level product category best fits this product?"
    if len(path) == 1:
        return f"Within the '{path[0]}' category, which subcategory best fits this product?"
    return f"Within '{path[0]} > {path[1]}', which specific category best fits this product?"


def _probabilities(state: dict, path: tuple[str, ...]) -> dict[str, float]:
    options = _options_at(path)
    if len(options) == 1:
        return {options[0]: 1.0}
    response = client.system_one(
        state=state,
        questions={
            "next": Choice(
                instructions=_instructions_for(path),
                criteria={option: None for option in options},
            )
        },
        model=MODEL,
    )
    return response.choices["next"].probabilities


def classify(title: str, description: str) -> str:
    state = {"title": title, "description": description}
    beam = [{"path": (), "score": 1.0}]

    for _ in range(3):
        with ThreadPoolExecutor(max_workers=len(beam)) as executor:
            distributions = list(
                executor.map(lambda candidate: _probabilities(state, candidate["path"]), beam)
            )

        candidates = [
            {"path": candidate["path"] + (label,), "score": candidate["score"] * probability}
            for candidate, probabilities in zip(beam, distributions)
            for label, probability in probabilities.items()
        ]
        beam = sorted(candidates, key=lambda candidate: candidate["score"], reverse=True)[:BEAM_WIDTH]

    return " > ".join(beam[0]["path"])
