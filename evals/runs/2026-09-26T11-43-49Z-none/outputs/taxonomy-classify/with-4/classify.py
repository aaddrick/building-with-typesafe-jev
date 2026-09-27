import json
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"


def _load_taxonomy() -> dict:
    with open(_TAXONOMY_PATH) as f:
        return json.load(f)


def classify(title: str, description: str) -> str:
    """Classify a product into a leaf category using typesafe.ai's Jev model.

    The taxonomy has ~1200 leaves, well past the Choice primitive's 255-option
    limit, so the category is narrowed in three hierarchical Choice calls:
    top-level category, then subcategory, then leaf.
    """
    taxonomy = _load_taxonomy()
    state = f"Product title: {title}\nProduct description: {description}"

    with TypeSafeClient() as client:
        top_response = client.system_one(
            state=state,
            questions={
                "category": Choice(
                    instructions="Which top-level product category best fits this product?",
                    criteria={name: None for name in taxonomy},
                ),
            },
        )
        top = top_response.answers["category"].choice
        subcategories = taxonomy[top]

        sub_response = client.system_one(
            state=state,
            questions={
                "subcategory": Choice(
                    instructions=f"Within the '{top}' category, which subcategory best fits this product?",
                    criteria={name: None for name in subcategories},
                ),
            },
        )
        sub = sub_response.answers["subcategory"].choice
        leaves = subcategories[sub]

        leaf_response = client.system_one(
            state=state,
            questions={
                "leaf": Choice(
                    instructions=f"Within '{top} > {sub}', which specific leaf category best fits this product?",
                    criteria={name: None for name in leaves},
                ),
            },
        )
        leaf = leaf_response.answers["leaf"].choice

    return f"{top} > {sub} > {leaf}"
