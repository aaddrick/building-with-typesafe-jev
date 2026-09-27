import json
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY_PATH = Path(__file__).with_name("taxonomy.json")
_TAXONOMY = json.loads(_TAXONOMY_PATH.read_text())


def _pick(client: TypeSafeClient, state: dict, instructions: str, options: list[str]) -> str:
    response = client.system_one(
        state=state,
        questions={
            "pick": Choice(
                instructions=instructions,
                criteria={option: option for option in options},
            ),
        },
    )
    return response.answers["pick"].choice


def classify(title: str, description: str) -> str:
    state = {"title": title, "description": description}

    with TypeSafeClient() as client:
        top = _pick(
            client,
            state,
            "Which top-level product category best fits this product?",
            list(_TAXONOMY.keys()),
        )

        subcategories = _TAXONOMY[top]
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
            f"Within '{top} > {sub}', which specific leaf category best fits this product?",
            leaves,
        )

    return f"{top} > {sub} > {leaf}"
