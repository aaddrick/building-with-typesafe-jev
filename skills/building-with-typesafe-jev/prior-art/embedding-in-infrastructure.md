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
- pg-jev (Postgres extension): [realZachi/pg-jev](https://github.com/realZachi/pg-jev), [pgjev.com](https://pgjev.com)
- sqlite-jev (extension + virtual table): [mgaitan/sqlite-jev](https://github.com/mgaitan/sqlite-jev)
- mysql-ailike (`AILIKE` plugin): [maayanlevy/mysql-ailike](https://github.com/maayanlevy/mysql-ailike), [HN](https://news.ycombinator.com/item?id=49774592)
- duckdb-jev: [colliber/duckdb-jev](https://github.com/colliber/duckdb-jev). JevQL: [kylemclaren/jevql](https://github.com/kylemclaren/jevql), [flaviocopes.com](https://flaviocopes.com/jev/). vgi-typesafe: [Query-farm/vgi-typesafe](https://github.com/Query-farm/vgi-typesafe)
- neo4jev (graph walking): [jexp/neo4jev](https://github.com/jexp/neo4jev)
- LanceDB `TypeSafeReranker`: [lancedb/lancedb](https://github.com/lancedb/lancedb) `python/python/lancedb/rerankers/typesafe.py`. OpenViking reranker: [volcengine/OpenViking](https://github.com/volcengine/OpenViking)

**Frameworks and agent stacks**
- LangChain middleware (auto mode, model routing): [langchain.com](https://www.langchain.com/blog/building-a-harness-with-jev)
- Pydantic AI provider: [pydantic.dev](https://pydantic.dev/docs/ai/models/typesafe/)
- Vercel AI Gateway: [vercel.com](https://vercel.com/changelog/typesafe-ai-jev-now-available-on-ai-gateway). Cloudflare: [developers.cloudflare.com](https://developers.cloudflare.com/ai/models/typesafe/jev/). Netlify: [netlify.com](https://www.netlify.com/changelog/typesafe-jev-ai-gateway/)
- AutoGPT blocks ([Significant-Gravitas/AutoGPT](https://github.com/Significant-Gravitas/AutoGPT)), Composio provider ([ComposioHQ/composio](https://github.com/ComposioHQ/composio)), pipecat classifier ([pipecat-ai/pipecat](https://github.com/pipecat-ai/pipecat)), fastmcp transform ([PrefectHQ/fastmcp](https://github.com/PrefectHQ/fastmcp)), dspy ([stanfordnlp/dspy](https://github.com/stanfordnlp/dspy)), OpenClaw plugin ([openclaw/openclaw](https://github.com/openclaw/openclaw)), deer-flow guardrails ([bytedance/deer-flow](https://github.com/bytedance/deer-flow)), oh-my-claudecode hooks ([Yeachan-Heo/oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode))
- ai-hedge-fund provider adapter (typed answers → existing JSON contract): [virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) `hedge_fund/llm/client.py`
- jevexpress (Express router): [carllippert/jev-router](https://github.com/carllippert/jev-router). Mastra moderation: [CodeAlive-AI/mastra-jev-moderation](https://github.com/CodeAlive-AI/mastra-jev-moderation)
- MCP servers wrapping Jev: [jkudish/jev-mcp](https://github.com/jkudish/jev-mcp), [blakestone-x/jev-mcp](https://github.com/blakestone-x/jev-mcp), [burnigtm/jev-mcp](https://github.com/burnigtm/jev-mcp). Simon Willison's `llm-typesafe`: [simonwillison.net](https://simonwillison.net/2026/Sep/22/llm-typesafe/)

**Products embedding Jev**
- Chatwoot ([chatwoot/chatwoot](https://github.com/chatwoot/chatwoot)), inbox-zero ([elie222/inbox-zero](https://github.com/elie222/inbox-zero)), worldmonitor ([koala73/worldmonitor](https://github.com/koala73/worldmonitor)), PostHog (experiments only; [PostHog/posthog](https://github.com/PostHog/posthog)), twenty CRM ([twentyhq/twenty](https://github.com/twentyhq/twenty)), Lightdash ([lightdash/lightdash](https://github.com/lightdash/lightdash)), OneDev ([theonedev/onedev](https://github.com/theonedev/onedev)), pdf-craft ([oomol-lab/pdf-craft](https://github.com/oomol-lab/pdf-craft)), Math-To-Manim ([HarleyCoops/Math-To-Manim](https://github.com/HarleyCoops/Math-To-Manim))

**CI and dev loop**
- Migration guard: [opaielsheikh/typesafe-migration-guard](https://github.com/opaielsheikh/typesafe-migration-guard). jev-commit: [valentynkit/jev-commit](https://github.com/valentynkit/jev-commit). pytest-jev: [allebee/pytest-jev](https://github.com/allebee/pytest-jev). oxlint-plugin-jev: [wobsoriano/oxlint-plugin-jev](https://github.com/wobsoriano/oxlint-plugin-jev). Perch: [lakeday-org/perch](https://github.com/lakeday-org/perch)

**Home and desktop**
- HA-Jev (sensors, automation actions, Assist agent): [AboveColin/HA-Jev](https://github.com/AboveColin/HA-Jev)
- Self-sorting Downloads folder: [x.com/marcelpociot](https://x.com/marcelpociot/status/2100906882365788167)

**Ecosystem ports** (for non-Python/JS hosts)
- Community SDKs in Go ([Stumble/jev-go](https://github.com/Stumble/jev-go)), Rust (jev-rs [HN](https://news.ycombinator.com/item?id=49814797)), Java/Spring ([HN](https://news.ycombinator.com/item?id=49762324)), .NET ([Hawxy/TypeSafeAI.Net](https://github.com/Hawxy/TypeSafeAI.Net)), Ruby ([HN](https://news.ycombinator.com/item?id=49757734)), PHP/Laravel ([Butochnikov/laravel-typesafe-jev](https://github.com/Butochnikov/laravel-typesafe-jev)), Elixir/OTP ([dannote/jev](https://github.com/dannote/jev)), Swift ([d-date/swift-jev](https://github.com/d-date/swift-jev)), R ([mountainMath/JevR](https://github.com/mountainMath/JevR)), PowerShell ([dfinke/Jev](https://github.com/dfinke/Jev)), Dart ([Solido/jev_dart](https://github.com/Solido/jev_dart)), Haskell ([realbogart/jev](https://github.com/realbogart/jev)), C++ ([pewriebontal/typesafe-sdk-cpp](https://github.com/pewriebontal/typesafe-sdk-cpp))
- Local and open clones for offline hosts: Ollaya ([HN](https://news.ycombinator.com/item?id=49848269)), Laya ([HN](https://news.ycombinator.com/item?id=49767430)), decider-4b ([Mapika/decider](https://github.com/Mapika/decider)), NanoJev ([TianyuCodings/NanoJev](https://github.com/TianyuCodings/NanoJev))
