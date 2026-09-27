# Shape: Embedding Jev in Existing Infrastructure

**Use when** you want Jev to feel native inside a host system: SQL, a vector DB, a web framework, CI, an agent framework, a home-automation hub, a browser.

## The shape

Wrap one `system_one` call as the host's own primitive:

| Host | Native primitive | Example |
|---|---|---|
| SQL database | predicate / scalar function | `WHERE jev(row, 'the name is European')` |
| Vector DB / search | reranker class | `TypeSafeReranker` |
| Web framework | router / middleware | Jev picks the handler |
| Agent framework | middleware / guardrail hook / block | tool-call gate, model router |
| CI / git | hook / plugin / lint rule | commit, migration, and semantic lint checks |
| Home automation | sensor / automation action / conversation agent | answers as entities |
| Browser | extension content script | per-element or per-post labels |
| Test runner | plugin | test-claim checks |

```python
# Sketch: a SQLite scalar function (per-row call; cache aggressively, filter in SQL first)
import functools, json, sqlite3
from typesafe_sdk import Noul, TypeSafeClient

client = TypeSafeClient()

@functools.lru_cache(maxsize=100_000)
def _jev(row_json: str, predicate: str) -> float:
    r = client.system_one(state={"row": json.loads(row_json)},
                          questions={"p": Noul(instructions=f"Is this true of `row`: {predicate}")})
    return r.nouls["p"].noul

db = sqlite3.connect("app.db")
db.create_function("jev", 2, _jev, deterministic=True)
# SELECT * FROM people WHERE country = 'DE' AND jev(json_object('name', name), 'the name is European') > 0.7
```

## Field lessons

- A per-row call is one HTTP request per row. Filter with ordinary SQL first, cache results, and batch where the host allows it (many rows as questions over one state, within the 32k limit).
- Mark the function deterministic only with a pinned model version. The alias moves.
- In any client-side host (browser, mobile), the API key is exposed. Proxy through a server. The JS SDK needs `dangerouslyAllowBrowser` for a reason.
- Home automation users push back on cloud round-trips. Offer a local fallback.
- The strongest adoption signal is Jev inside established OSS behind a feature flag or optional provider, not Jev-first products.

## Prior art

**Databases and search**
- pg-jev (Postgres extension): [realZachi/pg-jev](https://github.com/realZachi/pg-jev), pgjev.com
- sqlite-jev (extension + virtual table): [mgaitan/sqlite-jev](https://github.com/mgaitan/sqlite-jev)
- mysql-ailike (`AILIKE` plugin): [maayanlevy/mysql-ailike](https://github.com/maayanlevy/mysql-ailike), [HN](https://news.ycombinator.com/item?id=49774592)
- duckdb-jev, JevQL, vgi-typesafe (awesome-jev-typesafe, [flaviocopes.com](https://flaviocopes.com/jev/))
- neo4jev (graph walking): [jexp/neo4jev](https://github.com/jexp/neo4jev)
- LanceDB `TypeSafeReranker`, OpenViking reranker (in OSS)

**Frameworks and agent stacks**
- LangChain middleware (auto mode, model routing): [langchain.com](https://www.langchain.com/blog/building-a-harness-with-jev)
- Pydantic AI provider: [pydantic.dev](https://pydantic.dev/docs/ai/models/typesafe/)
- Vercel AI Gateway: [vercel.com](https://vercel.com/changelog/typesafe-ai-jev-now-available-on-ai-gateway). Cloudflare: [developers.cloudflare.com](https://developers.cloudflare.com/ai/models/typesafe/jev/). Netlify: [netlify.com](https://www.netlify.com/changelog/typesafe-jev-ai-gateway/)
- AutoGPT blocks, Composio provider, pipecat classifier, fastmcp transform, dspy, OpenClaw plugin, deer-flow guardrails, oh-my-claudecode hooks (in OSS; found by code search)
- ai-hedge-fund provider adapter (typed answers → existing JSON contract): virattt/ai-hedge-fund `hedge_fund/llm/client.py`
- jevexpress (Express router), Mastra moderation (npm / GitHub)
- MCP servers wrapping Jev (jkudish, blakestone-x, burnigtm). Simon Willison's `llm-typesafe`: [simonwillison.net](https://simonwillison.net/2026/Sep/22/llm-typesafe/)

**Products embedding Jev**
- Chatwoot, inbox-zero, worldmonitor, PostHog (experiments only), twenty CRM, Lightdash, OneDev, pdf-craft, Math-To-Manim (found by code search)

**CI and dev loop**
- Migration guard: [opaielsheikh/typesafe-migration-guard](https://github.com/opaielsheikh/typesafe-migration-guard). jev-commit, pytest-jev, oxlint-plugin-jev, Perch

**Home and desktop**
- HA-Jev (sensors, automation actions, Assist agent): [AboveColin/HA-Jev](https://github.com/AboveColin/HA-Jev)
- Self-sorting Downloads folder (X demo): [walidboulanouar/awesome-jev-use-cases](https://github.com/walidboulanouar/awesome-jev-use-cases)

**Ecosystem ports** (for non-Python/JS hosts)
- Community SDKs in Go, Rust (jev-rs [HN](https://news.ycombinator.com/item?id=49814797)), Java/Spring ([HN](https://news.ycombinator.com/item?id=49762324)), .NET, Ruby ([HN](https://news.ycombinator.com/item?id=49757734)), PHP/Laravel, Elixir/OTP, Swift, R, PowerShell, Dart, Haskell, C++
- Local and open clones for offline hosts: Ollaya ([HN](https://news.ycombinator.com/item?id=49848269)), Laya ([HN](https://news.ycombinator.com/item?id=49767430)), decider-4b, NanoJev
