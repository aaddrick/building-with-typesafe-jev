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
- Autoresearch feature discovery (LLM proposes → Jev answers → CatBoost): https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery.md
- 67 numeric columns from Jev answers (suggested): https://flaviocopes.com/jev/
- Demand forecasting and predictive features (idea): https://docs.typesafe.ai/concepts/use-case-map.md

**Research instruments**
- ENEM exam distractor psychometrics (option probabilities vs. real student choices): gh:Paulo83-dev/ARTIGO---PSICOMETRIA---JEV-CC-
- RST discourse relation labelling (34 labels, 2 Choices per span pair): gh:mkrupo/som_rst_parsing
- Jev-Mem agent-memory paper (UT Dallas): gh:libingzheren/Jev-Mem
- Clinical variable extraction, Jev as a baseline: gh:JunMa11/MedJev
- Systematic-review extraction with verbatim quotes: jev-reviewer (awesome-jev-typesafe)
- Engineering: CAD routing, FEM triage, DFM, BOM alignment: jev-for-engineers (awesome-jev-typesafe)

**Data curation**
- jev-curate, Rust streaming of Parquet/JSONL rubrics at >1,500 rows/s: gh:AkashPriyadarshii/jev-curate
- "blask datos labelling", the top app on OpenRouter's Jev page (about 26.7B tokens): https://openrouter.ai/typesafe/jev-1.13

**Benchmarks of Jev**
- OpenSanctions entity resolution: gh:panios/jev-opensanctions-benchmark
- Chess vs. NPC-addressee detection (out-of-lane vs. in-lane): gh:wondertwins/jev-benchmark
- Parallel vs. separate questions (identical answers, 12× cheaper batched): https://docs.typesafe.ai/cookbooks/parallel_questions.md
- Self-consistency vs. LLMs: https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook.md
- Calibration critiques (fair die, "30% risk"): HN:49830385, HN:49816899
- jevbench leaderboard (decider-4b slightly above Jev 1.13): HN:49849014
