import json
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"


def _load_taxonomy() -> dict:
    with open(TAXONOMY_PATH) as f:
        return json.load(f)


def _pick(client: TypeSafeClient, state: dict, instructions: str, options: list[str]) -> str:
    response = client.system_one(
        state=state,
        questions={
            "pick": Choice(
                instructions=instructions,
                criteria={option: None for option in options},
            ),
        },
    )
    return response.choices["pick"].choice


def classify(title: str, description: str) -> str:
    taxonomy = _load_taxonomy()
    state = {"title": title, "description": description}

    with TypeSafeClient() as client:
        top = _pick(
            client,
            state,
            "Which top-level product category best fits this product?",
            list(taxonomy.keys()),
        )
        subcategories = taxonomy[top]

        sub = _pick(
            client,
            state,
            f"Within the '{top}' category, which subcategory best fits this product?",
            list(subcategories.keys()),
        )
        leaves = subcategories[sub]

        leaf = _pick(
            client,
            state,
            f"Within '{top} > {sub}', which specific category best fits this product?",
            leaves,
        )

    return f"{top} > {sub} > {leaf}"
