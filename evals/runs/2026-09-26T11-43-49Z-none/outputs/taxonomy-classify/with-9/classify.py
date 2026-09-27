import json
import os
from functools import lru_cache

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY_PATH = os.path.join(os.path.dirname(__file__), "taxonomy.json")

_client = TypeSafeClient()


@lru_cache(maxsize=1)
def _load_taxonomy() -> dict:
    with open(_TAXONOMY_PATH) as f:
        return json.load(f)


def _choose(state: str, instructions: str, options: list[str]) -> str:
    response = _client.system_one(
        state=state,
        questions={
            "selection": Choice(
                instructions=instructions,
                criteria={option: None for option in options},
            ),
        },
    )
    return response.answers["selection"].choice


def classify(title: str, description: str) -> str:
    """Classify a product into its best-fit leaf category path, e.g. "Home > Kitchen > Knives"."""
    taxonomy = _load_taxonomy()
    state = f"Title: {title}\nDescription: {description}"

    top_level = _choose(
        state,
        "Which top-level product category best fits this item?",
        list(taxonomy.keys()),
    )
    subcategories = taxonomy[top_level]

    subcategory = _choose(
        state,
        f"Within the '{top_level}' category, which subcategory best fits this item?",
        list(subcategories.keys()),
    )
    leaves = subcategories[subcategory]

    leaf = _choose(
        state,
        f"Within '{top_level} > {subcategory}', which specific category best fits this item?",
        leaves,
    )

    return f"{top_level} > {subcategory} > {leaf}"
