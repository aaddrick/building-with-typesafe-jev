import json
import math
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY_PATH = Path(__file__).with_name("taxonomy.json")
_TAXONOMY: dict = json.loads(_TAXONOMY_PATH.read_text())

_BEAM_WIDTH = 3
_EPSILON = 1e-9

_client = TypeSafeClient()  # reads TYPESAFE_API_KEY; one client, reused across calls


def _children(path: tuple[str, ...]) -> dict[str, object]:
    """Direct children of `path`, keyed by name, valued by a description of
    what lives underneath (fed to Jev as Choice criteria so it can see into
    a branch before committing to it)."""
    node = _TAXONOMY
    for name in path:
        node = node[name]
    if isinstance(node, dict):
        return {name: list(val) if isinstance(val, list) else list(val.keys()) for name, val in node.items()}
    return {name: None for name in node}  # node is a flat list of leaf names


def _ask_children(state: dict, path: tuple[str, ...]) -> dict[str, float]:
    children = _children(path)
    keys = {f"c{i}": name for i, name in enumerate(children)}
    if not path:
        instructions = "Given `title` and `description`, which top-level product category best fits this product?"
    elif len(path) == 1:
        instructions = (
            f'This product is in the top-level category "{path[0]}". Given `title` and `description`, '
            f'which subcategory of "{path[0]}" best fits it?'
        )
    else:
        instructions = (
            f'This product is in "{" > ".join(path)}". Given `title` and `description`, '
            "which specific category best fits it?"
        )
    r = _client.system_one(
        state=state,
        questions={
            "next": Choice(instructions=instructions, criteria={key: children[name] for key, name in keys.items()}),
        },
    )
    probs = r.choices["next"].probabilities
    return {keys[k]: p for k, p in probs.items() if p > 0}


def classify(title: str, description: str) -> str:
    """Return the best-fitting leaf category path, e.g. "Home > Kitchen > Knives"."""
    state = {"title": title, "description": description}
    beams: list[tuple[tuple[str, ...], float]] = [((), 0.0)]  # (path, sum of log p)

    for _ in range(3):  # top-level -> subcategory -> leaf
        with ThreadPoolExecutor(max_workers=_BEAM_WIDTH) as pool:
            expansions = list(pool.map(lambda beam: _ask_children(state, beam[0]), beams))
        candidates = [
            (path + (name,), log_p + math.log(max(p, _EPSILON)))
            for (path, log_p), probs in zip(beams, expansions)
            for name, p in probs.items()
        ]
        beams = sorted(candidates, key=lambda b: b[1] / len(b[0]), reverse=True)[:_BEAM_WIDTH]

    best_path, _ = beams[0]
    return " > ".join(best_path)
