# Jev Patterns and Cookbook Techniques

Taken from docs.typesafe.ai/patterns and the 18 cookbooks, 2026-09-25. All thresholds below are the cookbooks' starting points. Each cookbook says to tune them on your own labeled data.

## The four official patterns

| Pattern | Shape | Use for |
|---|---|---|
| Speculative fan-out | Ask every question you might need in one call. Code reads only the branch it takes. | Triage, command parsing, any tree of decisions |
| Confidence-gated routing | A floor sends low confidence to a human. Above it, each action has its own bar, set by what a wrong action costs. | Actions with side effects |
| Composite scoring | One Score per dimension. Normalize with `score/(n-1)`. Weight in code. Re-weight without new calls. | Ranking, priority, resume screening |
| Intent routing | A cheap Choice in front of handlers: deterministic code, a specialist LLM, or a human | Keeping LLM spend for requests that need it |

## Techniques from the cookbooks

**Select, don't generate** (`pre_parsed_value_extraction`, `semantic_find`, `function_calling`).
A regex, parser, or LLM proposes candidates. The candidates become the Choice keys. Jev picks one, and code copies the exact string. Jev cannot invent a value or transpose a digit.

```python
criteria = {c: None for c in candidates} | {"none": "None of these is the requested value."}
```

Give the model the full candidate list. It cannot choose a value you left out.

**Pair a relative Choice with an absolute Noul** (`semantic_find`, `skill_suggestion`).
Choice probabilities sum to 1, so some option always wins, even when nothing fits. Add an `exists` / `fits` / `stated` Noul in the same request to decide whether to act at all.

**Put both sides of a relationship in one state** (`entity_alignment`, `classifying_rag_passages`, `citation_check`).
Use `{"entity_a": ..., "entity_b": ...}`, `{"query": ..., "passage": ...}`, or `{"claim": ..., "section": ...}`. One request per pair, many questions per request.

**Route on the nearest Score level** (`entity_alignment`).
`OUTCOME[min(int(score + 0.5), len(LEVELS) - 1)]`. When the levels are outcomes (different / maybe / same), no threshold constant is needed.

**Function calling** (`function_calling`).
- Tool: one `__tool__` Choice.
- `Literal` argument: a Choice whose keys are the exact accepted strings.
- `list[Literal]`: one Noul per member.
- `bool`: a Noul.
- Add a `stated` Noul per argument. When the user said nothing about it, the code keeps the default.
- Ints, free text, and dates get no question.
- Put all questions in one request (54 in the example). The confidence of the call is the minimum over the judgments the call used.

**Dates** (`date_extraction`).
Seven Choices in one call: mode (absolute / relative / none), month, day, year (with `none` and `out_of_range`), day_anchor, weekday, week_offset. Code assembles the date and does all calendar math, with `TODAY` pinned. The confidence of the date is the minimum over the parts used. Review below 0.60, or when the assembled date is impossible.

**Hierarchical classification** (`hierarchical_classification`, `classification_using_confidence`).
- Use one Choice per tree level: `criteria={f"c{i}": label}`, or each child's label plus its subtree as the option value. An opaque key hides the label, so never send the subtree alone. Skip nodes with one child.
- Beam search (K=3) scores each path as `prod(p) ** (1/decisions)`. The beam got 4/4 correct, greedy got 2/4.
- Cheaper alternative: when `confidence < 0.9`, report the parent category instead of the leaf. No second call.

**Verify-then-escalate cascade** (`sde_cascade`, `llm_guardrails`, `classifying_rag_passages`).
- A cheap LLM extracts. A Jev Noul battery checks each field, with keys like `field::hallucinated` or `field::format_violation`.
- If any per-field P(wrong) > 0.7, escalate to a strong reasoning LLM.
- Combine flags with **max, not average**. Averaging hides one bad field.
- A holistic "is this record good?" judge gave mushy scores (0.56, where the per-field checks gave 0.95 and 0.85).

**Guardrails as policy over cached probabilities** (`llm_guardrails`).
- Run hazard Nouls plus a severity Score on the input, and a separate battery on the output.
- Policies are threshold dicts: strict = review 0.35 / action 0.70 / severity ≥ 2.0 of 3; permissive = action 0.85.
- Re-route cached answers under a new policy with no API call.

**RAG passage filter** (`classifying_rag_passages`).
One request per (query, passage) with four Nouls. Route on the first rule that matches:
1. injection > 0.70: exclude.
2. contradicts > 0.70: put in a separate "conflicting" block.
3. relevant < 0.45: exclude.
4. evidence > 0.55: include.

No question asks "should I include this?". That decision stays in code. The injection Noul is not a security boundary.

**Re-ranking** (`rerank_typesafe`).
BM25 top-30, then one Noul per (query, candidate) with explicit `NoulCriteria`, then sort by `.noul`. Top-10 hit rate went from 38% to 62%. 1,200 calls cost $0.0645.

**Two-stage narrowing / progressive disclosure** (`skill_suggestion`, `autoformat`).
- Request 1: a Choice over all 182 options (short descriptions) plus gate Nouls.
- Request 2: the top 3 with full text, plus one absolute `fits::{name}` Noul each.
- A second request is justified only because request 2's state did not exist before request 1 answered.

**Classical ML on Jev features** (`autoresearch_feature_discovery`).
- An LLM proposes questions. Jev answers them for every row, one request per row.
- A Score becomes two features (mean level and SD). A Noul becomes one probability feature.
- Train CatBoost on them. RMSE was 1.77, against 2.15 when Jev predicted the target directly.

## Uncertainty handling

- **Noul band**: below 0.30 = no, 0.30–0.70 = human, above 0.70 = yes. A single 0.5 cutoff flips on noise: one question ranged 0.43–0.53 across 15 runs.
- **Choice abstain**: top probability below 0.60 → `uncertain`. With abstain, policy agreement rose from 90.8% to 99.2% across runs.
- **Confidence vs. top probability**: they differ. Choice confidence is `(n·top − 1)/(n − 1)`, so it depends only on the top probability and the option count (checked 2026-09-26 on 15 live Choice answers, within 0.01 rounding). A 0.45 winner next to a 0.44 runner-up gets the same confidence as a 0.45 winner with the rest spread thin. When that difference matters, compute a margin (top minus runner-up) from raw `probabilities`. Score confidence penalizes each level's probability by its distance from the top level, so a split between adjacent levels (`[.15, .63, .22, 0]` → 0.63) scores higher than the same top with far mass (`[.61, .23, .15, .01]` → 0.44). The formula is in `api-reference.md`. A two-way split between far-apart levels is a real disagreement. Route it to review even when the fractional `score` lands on a plausible middle level. Use `confidence` to decide whether to act.
- **Combining**: the minimum over the parts a decision uses. The maximum over "something is wrong" flags. A geometric mean for paths.

## Operations

- **Concurrency**: at most about 8 workers on a shared key. The public endpoint rate-limits above that.
- **Caching**: cache on (state, questions, model). Store tokens and `response.model`, not dollar amounts.
- **Timeouts**: the SDK default is 10 s. Cookbooks with large requests use 30–120 s.
- **Ties**: the API rounds every Noul, probability, and confidence to 0.01. Sorting hundreds of candidates by `.noul` produces ties. Break them with a second key, such as the retrieval rank.
- **Reproducibility**: pin the model ID and inputs such as `TODAY`. Answers are stable across runs (std ≈ 0.01), but values near a threshold still flip.
- **Speed**: measured 111–320 ms for 14–182-option requests, and 0.27 s for 13 questions over a 54k-character document. Batched calls were 12.2× cheaper and 10× faster than one question per call.
- **Stay under the limits**: 255 Choice options (one cookbook says "reliable up to roughly 240"; above that, chunk). 10 Score levels (11 returns an error). 32k tokens for state plus the longest question.

## Cookbook index (docs.typesafe.ai/cookbooks/<slug>.md)

| Need | Slug |
|---|---|
| Many questions in one call | `parallel_questions` |
| Stability across runs | `consistency_noul_cookbook`, `consistency_choice_cookbook` |
| Re-rank search results | `rerank_typesafe` |
| Find the line that answers | `semantic_find` |
| Rebuild paragraphs from text | `autoformat` |
| Natural language to a function call | `function_calling` |
| Pick a skill or tool from a roster | `skill_suggestion` |
| Entity matching / dedupe | `entity_alignment` |
| Filter RAG passages | `classifying_rag_passages` |
| Check a citation against its source | `citation_check` |
| Input/output guardrails | `llm_guardrails` |
| Check an LLM extraction, then escalate | `sde_cascade` |
| Extract dates | `date_extraction_cookbook` |
| Extract values from candidates | `pre_parsed_value_extraction_cookbook` |
| Deep taxonomy | `hierarchical_classification` |
| Fall back to a coarser label | `classification_using_confidence` |
| Features for a classical model | `autoresearch_feature_discovery` |
