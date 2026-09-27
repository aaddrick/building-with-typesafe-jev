"""Classify a product into a leaf category of taxonomy.json using TypeSafe's Jev model."""

import json
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"
_TAXONOMY = json.loads(_TAXONOMY_PATH.read_text())


def _choose(client: TypeSafeClient, state: dict, instructions: str, options: list[str]) -> str:
    response = client.system_one(
        state=state,
        questions={
            "category": Choice(
                instructions=instructions,
                criteria={name: None for name in options},
            )
        },
    )
    return response.choices["category"].choice


def classify(title: str, description: str) -> str:
    """Return the taxonomy path of the best-matching leaf category, e.g. "Home > Kitchen > Knives"."""
    state = {"title": title, "description": description}

    with TypeSafeClient() as client:
        top = _choose(
            client,
            state,
            "Which top-level product category does this product belong to?",
            list(_TAXONOMY.keys()),
        )
        subcategories = _TAXONOMY[top]

        sub = _choose(
            client,
            state,
            f"Within the '{top}' category, which subcategory does this product belong to?",
            list(subcategories.keys()),
        )
        leaves = subcategories[sub]

        leaf = _choose(
            client,
            state,
            f"Within '{top} > {sub}', which specific category best matches this product?",
            leaves,
        )

    return f"{top} > {sub} > {leaf}"
