import json
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"
_TAXONOMY: dict = json.loads(_TAXONOMY_PATH.read_text())


def classify(title: str, description: str) -> str:
    """Classify a product into the best-matching taxonomy leaf category.

    Walks the taxonomy top-down (category -> subcategory -> leaf) using
    Jev's Choice primitive at each level, since a single Choice call is
    capped at 255 options and the full tree has 1,200 leaves.
    """
    state = {"title": title, "description": description}

    with TypeSafeClient() as client:
        category = client.system_one(
            state=state,
            questions={
                "answer": Choice(
                    instructions="Which product category best fits this product?",
                    criteria={name: None for name in _TAXONOMY},
                ),
            },
        ).answers["answer"].choice

        subcategories = _TAXONOMY[category]
        subcategory = client.system_one(
            state=state,
            questions={
                "answer": Choice(
                    instructions=(
                        f"Within the '{category}' category, which subcategory "
                        "best fits this product?"
                    ),
                    criteria={name: None for name in subcategories},
                ),
            },
        ).answers["answer"].choice

        leaves = subcategories[subcategory]
        leaf = client.system_one(
            state=state,
            questions={
                "answer": Choice(
                    instructions=(
                        f"Within '{category} > {subcategory}', which specific "
                        "leaf category best fits this product?"
                    ),
                    criteria={name: None for name in leaves},
                ),
            },
        ).answers["answer"].choice

    return f"{category} > {subcategory} > {leaf}"
