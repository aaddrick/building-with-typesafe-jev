import json
from pathlib import Path

from typesafe_sdk import Choice, TypeSafeClient

_TAXONOMY = json.loads((Path(__file__).parent / "taxonomy.json").read_text())

_client = TypeSafeClient()


def classify(title: str, description: str) -> str:
    state = f"Title: {title}\nDescription: {description}"

    top = _choose(state, "Which top-level product category best fits this product?", _TAXONOMY)
    subcategories = _TAXONOMY[top]

    sub = _choose(state, f"Within '{top}', which subcategory best fits this product?", subcategories)
    leaves = subcategories[sub]

    leaf = _choose(state, f"Within '{top} > {sub}', which leaf category best fits this product?", leaves)

    return f"{top} > {sub} > {leaf}"


def _choose(state: str, instructions: str, options) -> str:
    result = _client.system_one(
        state=state,
        questions={"answer": Choice(instructions=instructions, criteria={name: None for name in options})},
    )
    return result.choices["answer"].choice
