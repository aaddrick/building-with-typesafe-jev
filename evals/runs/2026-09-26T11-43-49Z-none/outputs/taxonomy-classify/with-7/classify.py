import json
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"
_TAXONOMY: dict[str, dict[str, list[str]]] = json.loads(_TAXONOMY_PATH.read_text())


def classify(title: str, description: str) -> str:
    """Classify a product into a leaf category path using Jev, e.g. "Home > Kitchen > Knives"."""
    state = {"title": title, "description": description}

    with TypeSafeClient() as client:
        top_choice = client.system_one(
            state,
            {
                "top": Choice(
                    instructions="Which top-level product category best fits this item?",
                    criteria={name: None for name in _TAXONOMY},
                ),
            },
        ).choices["top"].choice
        subcategories = _TAXONOMY[top_choice]

        sub_choice = client.system_one(
            state,
            {
                "sub": Choice(
                    instructions=f"Within the '{top_choice}' category, which subcategory best fits this item?",
                    criteria={name: None for name in subcategories},
                ),
            },
        ).choices["sub"].choice
        leaves = subcategories[sub_choice]

        leaf_choice = client.system_one(
            state,
            {
                "leaf": Choice(
                    instructions=f"Within '{top_choice} > {sub_choice}', which specific category best fits this item?",
                    criteria={name: None for name in leaves},
                ),
            },
        ).choices["leaf"].choice

    return f"{top_choice} > {sub_choice} > {leaf_choice}"
