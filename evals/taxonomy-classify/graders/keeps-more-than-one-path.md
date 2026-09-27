---
type: llm
focus: { source: file, path: classify.py }
---

Field lesson "Beam beat greedy". Look at the walk down the tree.
PASS if the code keeps more than one candidate path at some level (beam search, top-k, or a fallback that revisits another branch when confidence is low).
FAIL if it commits greedily to the single top option at every level with no fallback.
FAIL if the file does not exist.
