"""Classify products into the taxonomy in taxonomy.json using TypeSafe's Jev model.

Uses hierarchical beam search over Choice questions (top-level category ->
subcategory -> leaf), scoring candidate paths by geometric-mean probability so
that a strong later decision can outweigh a weak/ambiguous earlier one. See
https://docs.typesafe.ai/cookbooks/hierarchical_classification.md.
"""

import json
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"
with open(_TAXONOMY_PATH) as _f:
    _TAXONOMY: dict = json.load(_f)

_BEAM_WIDTH = 3
_EPSILON = 1e-9


def _extend(candidate: dict, label: str, probability: float) -> dict:
    prob_product = candidate["prob_product"] * max(probability, _EPSILON)
    decisions = candidate["decisions"] + 1
    return {
        "path": candidate["path"] + (label,),
        "prob_product": prob_product,
        "decisions": decisions,
        "score": prob_product ** (1 / decisions),
    }


def classify(title: str, description: str) -> str:
    """Return the best-matching leaf category path, e.g. "Home > Kitchen > Knives"."""
    state = f"Product title: {title}\nDescription: {description}"

    with TypeSafeClient() as client:
        # Level 1: top-level category.
        result = client.system_one(
            state,
            {
                "category": Choice(
                    instructions="Which top-level product category best fits this product?",
                    criteria={name: None for name in _TAXONOMY},
                )
            },
        )
        probabilities = result.choices["category"].probabilities
        beam = sorted(
            (
                {"path": (name,), "prob_product": prob, "decisions": 1, "score": prob}
                for name, prob in probabilities.items()
            ),
            key=lambda c: c["score"],
            reverse=True,
        )[:_BEAM_WIDTH]

        # Level 2: subcategory, one Choice question per surviving beam candidate.
        questions = {
            f"c{i}": Choice(
                instructions=(
                    f"This product was placed in the '{candidate['path'][0]}' category. "
                    "Which subcategory best fits it?"
                ),
                criteria={name: None for name in _TAXONOMY[candidate["path"][0]]},
            )
            for i, candidate in enumerate(beam)
        }
        result = client.system_one(state, questions)
        expanded = [
            _extend(candidate, sub, prob)
            for i, candidate in enumerate(beam)
            for sub, prob in result.choices[f"c{i}"].probabilities.items()
        ]
        beam = sorted(expanded, key=lambda c: c["score"], reverse=True)[:_BEAM_WIDTH]

        # Level 3: leaf category, one Choice question per surviving beam candidate.
        questions = {
            f"c{i}": Choice(
                instructions=(
                    f"This product was placed in '{candidate['path'][0]} > {candidate['path'][1]}'. "
                    "Which specific category best fits it?"
                ),
                criteria={
                    name: None
                    for name in _TAXONOMY[candidate["path"][0]][candidate["path"][1]]
                },
            )
            for i, candidate in enumerate(beam)
        }
        result = client.system_one(state, questions)
        expanded = [
            _extend(candidate, leaf, prob)
            for i, candidate in enumerate(beam)
            for leaf, prob in result.choices[f"c{i}"].probabilities.items()
        ]
        best = max(expanded, key=lambda c: c["score"])

    return " > ".join(best["path"])
