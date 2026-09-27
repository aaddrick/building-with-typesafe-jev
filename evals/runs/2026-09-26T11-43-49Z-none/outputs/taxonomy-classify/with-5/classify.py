import json
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"
TAXONOMY = json.loads(TAXONOMY_PATH.read_text())


def classify(title: str, description: str) -> str:
    """Classify a product into the taxonomy, returning a path like "Home > Kitchen > Knives"."""
    state = {"title": title, "description": description}

    with TypeSafeClient() as client:
        category_response = client.system_one(
            state=state,
            questions={
                "category": Choice(
                    instructions="Which top-level product category best fits this product?",
                    criteria={name: None for name in TAXONOMY},
                ),
            },
        )
        category = category_response.answers["category"].choice

        subcategories = TAXONOMY[category]
        subcategory_response = client.system_one(
            state=state,
            questions={
                "subcategory": Choice(
                    instructions=(
                        f"Within the '{category}' category, which subcategory best fits this product?"
                    ),
                    criteria={name: None for name in subcategories},
                ),
            },
        )
        subcategory = subcategory_response.answers["subcategory"].choice

        leaves = subcategories[subcategory]
        leaf_response = client.system_one(
            state=state,
            questions={
                "leaf": Choice(
                    instructions=(
                        f"Within '{category} > {subcategory}', which specific leaf "
                        "category best fits this product?"
                    ),
                    criteria={name: None for name in leaves},
                ),
            },
        )
        leaf = leaf_response.answers["leaf"].choice

    return f"{category} > {subcategory} > {leaf}"
