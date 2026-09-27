import json
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"
_BEAM_WIDTH = 3

_INSTRUCTIONS = (
    "A product listing is described by `title` and `description`. "
    "Which category best describes this product?"
)


def _load_taxonomy() -> dict:
    with open(_TAXONOMY_PATH) as f:
        return json.load(f)


def _children(taxonomy: dict, path: tuple[str, ...]) -> list[str]:
    node = taxonomy
    for key in path:
        node = node[key]
    return list(node) if isinstance(node, dict) else list(node)


def _ask(client: TypeSafeClient, state: dict, labels: list[str]) -> dict[str, float]:
    response = client.system_one(
        state=state,
        questions={
            "category": Choice(
                instructions=_INSTRUCTIONS,
                criteria={label: None for label in labels},
            )
        },
        model="jev-latest",
    )
    return response.answers["category"].probabilities


def _expand(
    client: TypeSafeClient,
    state: dict,
    taxonomy: dict,
    beam: list[tuple[tuple[str, ...], float]],
) -> list[tuple[tuple[str, ...], float]]:
    candidates = []
    for path, path_score in beam:
        labels = _children(taxonomy, path)
        probabilities = _ask(client, state, labels)
        for label, probability in probabilities.items():
            candidates.append((path + (label,), path_score * probability))
    candidates.sort(key=lambda candidate: candidate[1], reverse=True)
    return candidates[:_BEAM_WIDTH]


def classify(title: str, description: str) -> str:
    """Return the best-matching leaf category path, e.g. "Home > Kitchen > Knives"."""
    taxonomy = _load_taxonomy()
    state = {"title": title, "description": description}

    with TypeSafeClient() as client:
        beam: list[tuple[tuple[str, ...], float]] = [((), 1.0)]
        for _ in range(3):  # top-level, subcategory, leaf
            beam = _expand(client, state, taxonomy, beam)

    best_path, _ = max(beam, key=lambda candidate: candidate[1])
    return " > ".join(best_path)
