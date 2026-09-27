# Shape: Ranking, Matching, and Walking

**Use when** you must order candidates, decide whether two records are the same, or navigate a graph or taxonomy.

## The shapes

**Rerank**: retrieve a shortlist in code (BM25, vectors), then ask a Noul per (query, candidate) and sort by `.noul`. The same value also prunes: drop anything below a threshold.

**Match / dedupe**: put both records in one state, then ask a Score with outcome levels (different / maybe / same) plus field-level Nouls. Route to the nearest level.

**Walk**: at each node, a Choice over the children or outgoing edges, plus a "goal reached?" Noul. Beam search keeps the top K paths.

```python
import math
from typesafe_sdk import Choice, Noul, TypeSafeClient

def walk(client: TypeSafeClient, doc: str, tree: dict, k: int = 3) -> list[tuple[list[str], float]]:
    beams = [([], 0.0)]                                    # (path, sum of log p)
    while any(_children(tree, p) for p, _ in beams):
        nxt = []
        for path, lp in beams:
            kids = _children(tree, path)
            if not kids:
                nxt.append((path, lp)); continue
            keys = {f"c{i}": name for i, name in enumerate(kids)}
            r = client.system_one(
                state={"document": doc},
                questions={"next": Choice(
                    instructions="Which direct child category best matches `document`?",
                    criteria={key: {"category": name, "subtree": kids[name]}  # the key hides the name
                              for key, name in keys.items()},
                )},
            )
            for key, p in r.choices["next"].probabilities.items():
                if p > 0:
                    nxt.append((path + [keys[key]], lp + math.log(p)))
        beams = sorted(nxt, key=lambda b: b[1] / max(len(b[0]), 1), reverse=True)[:k]
    return beams
```

`_children(tree, path)` returns a dict of `{child_name: subtree_or_description}`. The beam ranks paths by the geometric mean of their probabilities.

## Field lessons

- Rerank on a shortlist, never on the whole corpus. BM25 top-30 + a Noul per pair lifted top-10 hits from 38% to 62% for $0.0645 per 1,200 pairs.
- Ask several questions per pair in the same call (relevant, contains evidence, contradicts, injection).
- For entity resolution, block first (cheap keys), then pair-score. Keep numeric comparisons (ABV, dates, amounts) in code.
- Score levels named as outcomes remove the need for a threshold: `OUTCOME[round(score)]`.
- Beam (K=3) beat greedy 4/4 vs. 2/4 on the taxonomy walk. Showing subtrees in the option descriptions lets the model see what lives under a branch.
- Choice probabilities are relative. For "is anything relevant at all?", add an absolute Noul.

## Prior art

**Rerank and retrieval**
- Rerank cookbook, BM25 top-30 + Noul, top-10 38% → 62%: [docs.typesafe.ai](https://docs.typesafe.ai/cookbooks/rerank_typesafe.md)
- RAG passage classifier, 4 Nouls per passage with first-match routing: [docs.typesafe.ai](https://docs.typesafe.ai/cookbooks/classifying_rag_passages.md)
- LanceDB `TypeSafeReranker` ([`lancedb/rerankers/typesafe.py`](https://github.com/lancedb/lancedb/blob/main/python/python/lancedb/rerankers/typesafe.py) in [lancedb/lancedb](https://github.com/lancedb/lancedb)), OpenViking [`jev_rerank.py`](https://github.com/volcengine/OpenViking/blob/main/openviking/models/rerank/jev_rerank.py) in [volcengine/OpenViking](https://github.com/volcengine/OpenViking), [hev/reranker](https://github.com/hev/reranker)
- Jev in production vs. a cross-encoder: [HN](https://news.ycombinator.com/item?id=49804788)
- Search planner (sources, time range, query terms, then rank): [superagents-lab/jev-search](https://github.com/superagents-lab/jev-search)
- Federated retrieval routing gated at 0.6: [Bonzokoles/36_chambers](https://github.com/Bonzokoles/36_chambers)
- fastmcp [`jev_search` transform](https://github.com/PrefectHQ/fastmcp/blob/main/fastmcp_slim/fastmcp/experimental/transforms/jev_search.py) in [PrefectHQ/fastmcp](https://github.com/PrefectHQ/fastmcp)

**Match and dedupe**
- Entity alignment cookbook (Score outcomes + companion Nouls): [docs.typesafe.ai](https://docs.typesafe.ai/cookbooks/entity_alignment.md)
- OpenSanctions entity-resolution benchmark: [panios/jev-opensanctions-benchmark](https://github.com/panios/jev-opensanctions-benchmark)
- jlink, English match rules across datasets: [keltokhy/jlink](https://github.com/keltokhy/jlink)
- Genealogy matching discussion (block first, Splink): [HN](https://news.ycombinator.com/item?id=49723461)
- Resume vs. duplicate candidate records: [docs.typesafe.ai](https://docs.typesafe.ai/primitives/noul.md) (structured instructions section)
- Dedupe reported "underwhelming": [HN](https://news.ycombinator.com/item?id=49842510)

**Walk graphs and taxonomies**
- Hierarchical classification with beam search: [docs.typesafe.ai](https://docs.typesafe.ai/cookbooks/hierarchical_classification.md)
- Coarse fallback (report the parent when confidence < 0.9): [docs.typesafe.ai](https://docs.typesafe.ai/cookbooks/classification_using_confidence.md)
- neo4jev, edges as a Choice + "goal reached?" Noul, beam over log-probs: [jexp/neo4jev](https://github.com/jexp/neo4jev)
- jev-tree, one Choice per level past the 255 cap: [reachjalil/jev-tree](https://github.com/reachjalil/jev-tree)
- Wikiracing via links: [typesafe.ai](https://typesafe.ai/blog/introducing-system-one-models-and-jev)

**Ranking people and things**
- Composite scoring (resume screening weights): [docs.typesafe.ai](https://docs.typesafe.ai/patterns/composite-scoring.md)
- 700 leads scored in 40 s: [x.com/romanbuildsaas](https://x.com/romanbuildsaas/status/2100891604735099103). 400 companies matched to one candidate: [x.com/sarvagya_kul](https://x.com/sarvagya_kul/status/2100980770206879849)
- Nifty 50 re-rank every 15 s: [arimanyus/warrenduffer](https://github.com/arimanyus/warrenduffer)
- "Poor man's ranking", top 5 of 1,000 articles (idea): [HN](https://news.ycombinator.com/item?id=49722440)
