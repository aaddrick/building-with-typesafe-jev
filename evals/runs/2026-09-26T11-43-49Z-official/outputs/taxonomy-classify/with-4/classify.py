"""Classify product listings into the taxonomy defined in taxonomy.json using typesafe.ai's Jev model."""

import json
from pathlib import Path
from typing import Iterable

from typesafe_sdk import Choice, TypeSafeClient

TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"
MODEL = "jev-latest"

with open(TAXONOMY_PATH) as f:
    TAXONOMY: dict = json.load(f)


def classify(title: str, description: str) -> str:
    """Return the taxonomy path of the best-matching leaf category, e.g. "Home > Kitchen > Knives"."""
    state = {"title": title, "description": description}

    with TypeSafeClient() as client:
        top = _choose(client, state, TAXONOMY.keys(), "top-level category")
        subcategories = TAXONOMY[top]
        sub = _choose(client, state, subcategories.keys(), "subcategory")
        leaves = subcategories[sub]
        leaf = _choose(client, state, leaves, "leaf category")

    return f"{top} > {sub} > {leaf}"


def _choose(client: TypeSafeClient, state: dict, options: Iterable[str], level: str) -> str:
    response = client.system_one(
        state=state,
        questions={
            "category": Choice(
                instructions=(
                    f"Given the product `title` and `description`, which {level} "
                    "best describes this product?"
                ),
                criteria={option: None for option in options},
            )
        },
        model=MODEL,
    )
    return response.choices["category"].choice
