import json
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY = json.loads((Path(__file__).parent / "taxonomy.json").read_text())


def classify(title: str, description: str) -> str:
    """Classify a product into the best-matching leaf category path, e.g. "Home > Kitchen > Knives"."""
    state = f"Title: {title}\nDescription: {description}"

    with TypeSafeClient() as client:
        category_answer = client.system_one(
            state=state,
            questions={
                "category": Choice(
                    instructions="Which top-level product category best fits this item?",
                    criteria={name: None for name in _TAXONOMY},
                ),
            },
        ).choices["category"]
        category = category_answer.choice

        subcategories = _TAXONOMY[category]
        subcategory_answer = client.system_one(
            state=state,
            questions={
                "subcategory": Choice(
                    instructions=f"Within the '{category}' category, which subcategory best fits this item?",
                    criteria={name: None for name in subcategories},
                ),
            },
        ).choices["subcategory"]
        subcategory = subcategory_answer.choice

        leaves = subcategories[subcategory]
        leaf_answer = client.system_one(
            state=state,
            questions={
                "leaf": Choice(
                    instructions=f"Within '{category} > {subcategory}', which specific leaf category best fits this item?",
                    criteria={name: None for name in leaves},
                ),
            },
        ).choices["leaf"]
        leaf = leaf_answer.choice

    return f"{category} > {subcategory} > {leaf}"
