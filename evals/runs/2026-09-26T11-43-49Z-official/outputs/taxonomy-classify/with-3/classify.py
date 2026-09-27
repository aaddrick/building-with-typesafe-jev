import json
from dataclasses import dataclass, field
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"
_TAXONOMY: dict = json.loads(_TAXONOMY_PATH.read_text())

_BEAM_WIDTH = 3


@dataclass
class _Candidate:
    path: tuple[str, ...]
    node: dict | list
    edge_probs: list[float] = field(default_factory=list)

    @property
    def score(self) -> float:
        product = 1.0
        for p in self.edge_probs:
            product *= p
        return product ** (1 / len(self.edge_probs))


def _options(node: dict | list) -> list[str]:
    return list(node.keys()) if isinstance(node, dict) else list(node)


def _expand(client: TypeSafeClient, state: dict, candidates: list[_Candidate]) -> list[_Candidate]:
    questions = {}
    for i, candidate in enumerate(candidates):
        location = " > ".join(candidate.path) if candidate.path else "the top level"
        questions[f"c{i}"] = Choice(
            instructions=(
                "Considering the product's `title` and `description`, which of these "
                f"categories is the best next-level match under {location}?"
            ),
            criteria={option: None for option in _options(candidate.node)},
        )

    response = client.system_one(state, questions)

    expanded: list[_Candidate] = []
    for i, candidate in enumerate(candidates):
        answer = response.choices[f"c{i}"]
        for option in _options(candidate.node):
            child_node = candidate.node[option] if isinstance(candidate.node, dict) else None
            expanded.append(
                _Candidate(
                    path=candidate.path + (option,),
                    node=child_node,
                    edge_probs=candidate.edge_probs + [answer.probabilities[option]],
                )
            )

    expanded.sort(key=lambda c: c.score, reverse=True)
    return expanded[:_BEAM_WIDTH]


def classify(title: str, description: str) -> str:
    state = {"title": title, "description": description}

    with TypeSafeClient() as client:
        candidates = [_Candidate(path=(), node=_TAXONOMY)]
        for _ in range(3):  # top-level category, subcategory, leaf category
            candidates = _expand(client, state, candidates)

    best = max(candidates, key=lambda c: c.score)
    return " > ".join(best.path)
