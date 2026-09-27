"""Classify a product into a leaf category of taxonomy.json using typesafe.ai's Jev model."""

import json
import math
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"
BEAM_WIDTH = 3

_client: TypeSafeClient | None = None


def _get_client() -> TypeSafeClient:
    # Reused across calls: the SDK docs say to keep one long-lived client
    # rather than opening a connection per request.
    global _client
    if _client is None:
        _client = TypeSafeClient()
    return _client


def _load_taxonomy() -> dict:
    with open(TAXONOMY_PATH) as f:
        return json.load(f)


def _choose(client: TypeSafeClient, state: dict, instructions: str, options: dict) -> dict[str, float]:
    r = client.system_one(
        state=state,
        questions={"pick": Choice(instructions=instructions, criteria=options)},
    )
    return r.choices["pick"].probabilities


def classify(title: str, description: str) -> str:
    """Return the best leaf category path, e.g. "Home > Kitchen > Knives"."""
    taxonomy = _load_taxonomy()
    state = {"title": title, "description": description}
    client = _get_client()

    # The tree is 3 levels deep and each level fits under the 255-option Choice
    # cap, but the options at level 2/3 depend on the level above, so each
    # level needs its own request. Beam search (rather than greedy) carries
    # the top candidates forward since an early near-tie can flip once the
    # model sees the next level's options.
    top_options = {top: list(subs.keys()) for top, subs in taxonomy.items()}
    probs = _choose(
        client, state,
        "Which top-level product category best fits `title` and `description`?",
        top_options,
    )
    beams = sorted(
        ([top], math.log(p)) for top, p in probs.items() if p > 0
    )
    beams = sorted(beams, key=lambda b: b[1], reverse=True)[:BEAM_WIDTH]

    next_beams = []
    for path, lp in beams:
        (top,) = path
        sub_options = dict(taxonomy[top])
        probs = _choose(
            client, state,
            f"Within the `{top}` category, which subcategory best fits `title` and `description`?",
            sub_options,
        )
        next_beams.extend(
            (path + [sub], lp + math.log(p)) for sub, p in probs.items() if p > 0
        )
    beams = sorted(next_beams, key=lambda b: b[1], reverse=True)[:BEAM_WIDTH]

    next_beams = []
    for path, lp in beams:
        top, sub = path
        leaf_options = {leaf: None for leaf in taxonomy[top][sub]}
        probs = _choose(
            client, state,
            f"Within `{top} > {sub}`, which specific category best fits `title` and `description`?",
            leaf_options,
        )
        next_beams.extend(
            (path + [leaf], lp + math.log(p)) for leaf, p in probs.items() if p > 0
        )
    beams = sorted(next_beams, key=lambda b: b[1], reverse=True)

    best_path, _ = beams[0]
    return " > ".join(best_path)
