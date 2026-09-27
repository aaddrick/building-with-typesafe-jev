---
type: llm
focus: { source: file, path: classify.py }
---

Row "More than 255 options". Jev's Choice accepts at most 255 options, and this taxonomy has 1,200 leaves.
PASS if no single Choice can receive more than 255 options: the code walks the tree level by level, or pre-ranks candidates in code and asks a Choice over at most 255 of them, or splits candidates into groups of at most 255 and compares the winners.
FAIL if the code builds one Choice over all leaves, or over any list that can exceed 255 options.
FAIL if the file does not exist.
