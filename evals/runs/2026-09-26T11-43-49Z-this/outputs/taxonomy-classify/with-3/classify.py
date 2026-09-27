import json
import math
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"
_TAXONOMY: dict = json.loads(_TAXONOMY_PATH.read_text())

_client: TypeSafeClient | None = None


def _get_client() -> TypeSafeClient:
    global _client
    if _client is None:
        _client = TypeSafeClient()
    return _client


def _children(path: list[str]) -> dict[str, object]:
    """Direct children of `path` in the taxonomy, as {name: description}."""
    if len(path) == 0:
        return {top: {"subcategories": list(subs)} for top, subs in _TAXONOMY.items()}
    if len(path) == 1:
        subs = _TAXONOMY[path[0]]
        return {sub: {"leaves": leaves} for sub, leaves in subs.items()}
    if len(path) == 2:
        leaves = _TAXONOMY[path[0]][path[1]]
        return {leaf: None for leaf in leaves}
    return {}


def classify(title: str, description: str, *, beam_width: int = 3) -> str:
    """Return the best leaf category path, e.g. "Home > Kitchen > Knives"."""
    state = {"title": title, "description": description}
    client = _get_client()
    beams: list[tuple[list[str], float]] = [([], 0.0)]

    for _ in range(3):  # top-level -> subcategory -> leaf
        candidates: list[tuple[list[str], float]] = []
        for path, log_prob in beams:
            kids = _children(path)
            keys = {f"c{i}": name for i, name in enumerate(kids)}
            response = client.system_one(
                state=state,
                questions={
                    "next": Choice(
                        instructions=(
                            "A product has the given `title` and `description`. "
                            "Which category below best fits this product?"
                        ),
                        criteria={key: kids[name] for key, name in keys.items()},
                    )
                },
            )
            probabilities = response.choices["next"].probabilities
            for key, name in keys.items():
                p = probabilities.get(key, 0.0)
                if p > 0:
                    candidates.append((path + [name], log_prob + math.log(p)))

        beams = sorted(candidates, key=lambda b: b[1], reverse=True)[:beam_width]

    best_path, _ = max(beams, key=lambda b: b[1])
    return " > ".join(best_path)
