# Shape: Jev Answers as Data

**Use when** the output is not an action but a measurement: features for a classical model, labels for a dataset, variables for a study, or a benchmark of Jev itself.

## The shape

```
rows → one request per row with N questions → a numeric table
     Noul  → 1 column (P(yes))
     Score → 2 columns (mean level, spread) or one column per level probability
     Choice→ one column per option probability
→ train (CatBoost/logistic), correlate with outcomes, or compare with human data
```

```python
def to_features(r) -> dict[str, float]:
    row = {}
    for qid, a in r.nouls.items():
        row[qid] = a.noul
    for qid, a in r.scores.items():
        mean = a.score
        row[f"{qid}_mean"] = mean
        row[f"{qid}_sd"] = sum(p * (lvl - mean) ** 2 for lvl, p in a.probabilities.items()) ** 0.5
    for qid, a in r.choices.items():
        row.update({f"{qid}={opt}": p for opt, p in a.probabilities.items()})
    return row
```

## Field lessons

- Many narrow features + a trained model beat asking Jev for the target directly (RMSE 1.77 vs. 2.15).
- An LLM can propose the candidate questions. Keep the ones that improve held-out error (an autoresearch loop).
- Research designs that use the calibrated probabilities themselves are a novel angle. Example: do option probabilities match how human test-takers distribute their answers?
- For studies, pin the model ID and report it. Measure run-to-run stability (std ≈ 0.01 reported) before you trust small effects.
- Calibration varies by domain. Check it against labels before you treat a probability as a frequency.

## Prior art

**Features and prediction**
- Autoresearch feature discovery (LLM proposes → Jev answers → CatBoost): [docs.typesafe.ai](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery.md)
- 67 numeric columns from Jev answers (suggested): [flaviocopes.com](https://flaviocopes.com/jev/)
- Demand forecasting and predictive features (idea): [docs.typesafe.ai](https://docs.typesafe.ai/concepts/use-case-map.md)

**Research instruments**
- ENEM exam distractor psychometrics (option probabilities vs. real student choices): [Paulo83-dev/ARTIGO---PSICOMETRIA---JEV-CC-](https://github.com/Paulo83-dev/ARTIGO---PSICOMETRIA---JEV-CC-)
- RST discourse relation labelling (34 labels, 2 Choices per span pair): [mkrupo/som_rst_parsing](https://github.com/mkrupo/som_rst_parsing)
- Jev-Mem agent-memory paper (UT Dallas): [libingzheren/Jev-Mem](https://github.com/libingzheren/Jev-Mem)
- Clinical variable extraction, Jev as a baseline: [JunMa11/MedJev](https://github.com/JunMa11/MedJev)
- Systematic-review extraction with verbatim quotes: [choxos/jev-reviewer](https://github.com/choxos/jev-reviewer)
- Engineering: CAD routing, FEM triage, DFM, BOM alignment: [Foadsf/jev-for-engineers](https://github.com/Foadsf/jev-for-engineers)

**Data curation**
- jev-curate, Rust streaming of Parquet/JSONL rubrics at >1,500 rows/s: [AkashPriyadarshii/jev-curate](https://github.com/AkashPriyadarshii/jev-curate)
- "blask datos labelling", the top app on OpenRouter's Jev page (about 26.7B tokens): [openrouter.ai](https://openrouter.ai/typesafe/jev-1.13)

**Benchmarks of Jev**
- OpenSanctions entity resolution: [panios/jev-opensanctions-benchmark](https://github.com/panios/jev-opensanctions-benchmark)
- Chess vs. NPC-addressee detection (out-of-lane vs. in-lane): [wondertwins/jev-benchmark](https://github.com/wondertwins/jev-benchmark)
- Parallel vs. separate questions (identical answers, 12× cheaper batched): [docs.typesafe.ai](https://docs.typesafe.ai/cookbooks/parallel_questions.md)
- Self-consistency vs. LLMs: [docs.typesafe.ai](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook.md)
- Calibration critiques (fair die, "30% risk"): [HN](https://news.ycombinator.com/item?id=49830385), [HN](https://news.ycombinator.com/item?id=49816899)
- jevbench leaderboard (decider-4b slightly above Jev 1.13): [HN](https://news.ycombinator.com/item?id=49849014)
