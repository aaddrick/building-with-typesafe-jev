# Shape: Stream Filters and Bulk Labelling

**Use when** you must label, filter, or route every item in a large or endless flow: social posts, emails, logs, rows, comments, DOM elements, headlines, applications.

## The shape

```
for each item (bounded concurrency, about 8 workers):
    one request: several speculative questions about this item
    code: threshold / label / drop / route; store the raw probabilities
```

```python
from concurrent.futures import ThreadPoolExecutor
from typesafe_sdk import Choice, Noul, TypeSafeClient

client = TypeSafeClient()
QUESTIONS = {
    "ai_written": Noul(instructions="Does `post` read as AI-generated filler rather than a person's own words?"),
    "promotional": Noul(instructions="Is `post` primarily promoting a product, service, or the author?"),
    "topic": Choice(instructions="What is `post` mainly about?",
                    criteria={"work": None, "tech": None, "politics": None, "personal": None, "other": None}),
}

def label(post: str) -> dict:
    r = client.system_one(state={"post": post}, questions=QUESTIONS)
    return {"ai": r.nouls["ai_written"].noul, "promo": r.nouls["promotional"].noul,
            "topic": r.choices["topic"].choice, "model": r.model}

with ThreadPoolExecutor(max_workers=8) as pool:
    labels = list(pool.map(label, posts))
hidden = [p for p, l in zip(posts, labels) if max(l["ai"], l["promo"]) > 0.8]
```

## Variants

- **User-tuned weights**: store the raw probabilities and let the user's own labels fit the weights or thresholds (slop-filter).
- **Per-DOM-element**: "is this element an ad?" in a browser extension. Batch many elements per request, one Noul per element, where one page is the state.
- **Log and code grep by meaning**: pre-filter with a regex or line window, then ask per line or chunk.
- **Bulk offline jobs**: resumes, papers, reviews, applications. Cache on (state, questions, model).
- **Periodic feeds**: poll headlines every N minutes and score them.

## Field lessons

- About 8 concurrent workers is the practical ceiling on a shared key before 429s.
- Cost references: about $0.00003 per social post; 500 emails for 3.5¢; 1M log lines for about $10 in about 10 minutes; 1,018 papers for 8¢; 724 ads in 40 s for 9¢; 3,518 applications in under 5 minutes.
- Put many questions in each request. The state (the item) dominates tokens, so extra questions are almost free.
- Take a hard look at "is this AI-written?" questions. They are vibes-level judgments. Calibrate on your own labels before hiding content.
- For offline bulk work, batched LLM prompts (20 records per call) can match Jev on cost ([HN](https://news.ycombinator.com/item?id=49821799)). Jev wins on latency and per-item isolation.

## Prior art

**Consumer filters (extensions)**
- sift, labels posts on X/LinkedIn/Reddit/YouTube for about $0.00003 per post: [bohutang/sift](https://github.com/bohutang/sift)
- slop-filter, weights fit to your labels: [adamnroman/slop-filter](https://github.com/adamnroman/slop-filter)
- Slop Mop (LinkedIn): [HN](https://news.ycombinator.com/item?id=49819820). Sniffslop: [HN](https://news.ycombinator.com/item?id=49813985)
- Ad blocker by meaning: [realZachi/typesafe-adblock](https://github.com/realZachi/typesafe-adblock)
- Scroll-time slop detector [x.com/RBilgil](https://x.com/RBilgil/status/2100976648552169805), YouTube sponsor skipper [x.com/tdinh_me](https://x.com/tdinh_me/status/2100793777103466615), plain-language X post hiding [x.com/marcelpociot](https://x.com/marcelpociot/status/2100520134481735729), Doomscroll Filter [x.com/robj3d3](https://x.com/robj3d3/status/2101074194260000982), reply-guy filter [x.com/iannuttall](https://x.com/iannuttall/status/2100888635943883244)
- Ground Truth article-framing overlay: [x.com](https://x.com/jagenaujagenau/status/2100622352333574460). Privacy Facts policy labels: [thenewpotato/privacy-facts](https://github.com/thenewpotato/privacy-facts)

**Moderation and anti-spam**
- Telegram bot that deletes only high-confidence spam: [backmeupplz/jev_antispam_bot](https://github.com/backmeupplz/jev_antispam_bot)
- Discord moderation bot "Soter": [HN](https://news.ycombinator.com/item?id=49825787). mastra-jev-moderation: [CodeAlive-AI/mastra-jev-moderation](https://github.com/CodeAlive-AI/mastra-jev-moderation)
- Trust and safety ideas (severity × confidence → allow/warn/review/block): [docs.typesafe.ai](https://docs.typesafe.ai/concepts/use-case-map.md)

**Email, support, CRM**
- Chatwoot conversation priority/labels: [`captain/conversation_classifier_service.rb`](https://github.com/chatwoot/chatwoot/blob/develop/app/services/captain/conversation_classifier_service.rb) in [chatwoot/chatwoot](https://github.com/chatwoot/chatwoot)
- inbox-zero decision model: [`utils/decision-model/typesafe.ts`](https://github.com/elie222/inbox-zero/blob/main/apps/web/utils/decision-model/typesafe.ts) in [elie222/inbox-zero](https://github.com/elie222/inbox-zero)
- Bryo AI email triage (Gemini slightly more accurate, 10–20× the cost): [marktechpost.com](https://www.marktechpost.com/2026/09/19/typesafe-ai-releases-jev/)
- Jevmail 5-tray Gmail sorter: [fazlerocks/jevmail](https://github.com/fazlerocks/jevmail)
- Support cost study: [HN](https://news.ycombinator.com/item?id=49794787). CraftCX write-up: [HN](https://news.ycombinator.com/item?id=49846104)

**Logs, code, security**
- Grev/jgrep "thinking grep", 1M log lines for about $10: [HN](https://news.ycombinator.com/item?id=49837132), [kyu1204/jgrep](https://github.com/kyu1204/jgrep)
- jev-semgrep with AND/OR/NOT and JA/EN: [uehaj/jev-semgrep](https://github.com/uehaj/jev-semgrep). askgrep: [fajarhide/askgrep](https://github.com/fajarhide/askgrep)
- SOC alert triage and grouping: [HN](https://news.ycombinator.com/item?id=49850990), [evals.typesafe.ai](https://evals.typesafe.ai/)

**Bulk business labelling**
- Ad teardown, 724 ads for 9¢ (Matthew Berman via [linas.substack.com](https://linas.substack.com/p/how-to-use-jev-ai))
- Resume vs. 6,245 YC companies for $0.37: [flaviocopes.com](https://flaviocopes.com/jev/)
- IRS forms across 261 classes: kyotofin ([gist.github.com](https://gist.github.com/drillan/6916b16e8ea31a8ec36c8f59d6483150))
- Forum DB curation for backlinks: [HN](https://news.ycombinator.com/item?id=49804096). Site SEO audit with 52 rules: [AgriciDaniel/jev-seo](https://github.com/AgriciDaniel/jev-seo)
- PDF classification and packet splitting: [jerryjliu/docjev](https://github.com/jerryjliu/docjev)
- CV screening with an editable policy: [gtaras7/typesafe-jev](https://github.com/gtaras7/typesafe-jev)
- Litigation discovery, 3 checks per page: [langchain.com](https://www.langchain.com/blog/building-prod-with-jev-and-langgraph)

**Feeds**
- worldmonitor headline threat level: [`shared/jev-classify.js`](https://github.com/koala73/worldmonitor/blob/main/shared/jev-classify.js) in [koala73/worldmonitor](https://github.com/koala73/worldmonitor)
- "Should AI Kill Us All?", headlines every 10 minutes: shouldaikillusall.com ([hellogumbo/should-ai-kill-us-all](https://github.com/hellogumbo/should-ai-kill-us-all))
