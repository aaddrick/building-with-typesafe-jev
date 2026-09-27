import json
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY_PATH = Path(__file__).parent / "taxonomy.json"
_TAXONOMY = json.loads(_TAXONOMY_PATH.read_text())


def classify(title: str, description: str) -> str:
    """Classify a product into a leaf category using Jev's Choice primitive.

    Walks the taxonomy tree top-down (top-level -> subcategory -> leaf),
    since a single Choice call supports at most 255 options and the full
    tree has 1200 leaves.
    """
    state = {"title": title, "description": description}

    with TypeSafeClient() as client:
        top_level = _choose(
            client,
            state,
            instructions="Which top-level product category does this item belong to?",
            criteria={
                name: ", ".join(subcats.keys())
                for name, subcats in _TAXONOMY.items()
            },
        )

        subcategories = _TAXONOMY[top_level]
        subcategory = _choose(
            client,
            state,
            instructions=f"Within '{top_level}', which subcategory does this item belong to?",
            criteria={
                name: ", ".join(leaves)
                for name, leaves in subcategories.items()
            },
        )

        leaves = subcategories[subcategory]
        leaf = _choose(
            client,
            state,
            instructions=f"Within '{top_level} > {subcategory}', which specific category best fits this item?",
            criteria={name: None for name in leaves},
        )

    return f"{top_level} > {subcategory} > {leaf}"


def _choose(client: TypeSafeClient, state: dict, instructions: str, criteria: dict) -> str:
    response = client.system_one(
        state=state,
        questions={"answer": Choice(instructions=instructions, criteria=criteria)},
    )
    return response.answers["answer"].choice
