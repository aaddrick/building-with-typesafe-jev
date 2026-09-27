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
- For offline bulk work, batched LLM prompts (20 records per call) can match Jev on cost (HN:49821799). Jev wins on latency and per-item isolation.

## Prior art

**Consumer filters (extensions)**
- sift, labels posts on X/LinkedIn/Reddit/YouTube for about $0.00003 per post: gh:bohutang/sift
- slop-filter, weights fit to your labels: gh:adamnroman/slop-filter
- Slop Mop (LinkedIn): HN:49819820. Sniffslop: HN:49813985
- Ad blocker by meaning: gh:realZachi/typesafe-adblock
- X demos: scroll-time slop detector, YouTube sponsor skipper, plain-language X post hiding, Doomscroll Filter, reply-guy filter (https://github.com/walidboulanouar/awesome-jev-use-cases)
- Ground Truth article-framing overlay (JevDirectory). Privacy Facts policy labels (awesome-jev-typesafe)

**Moderation and anti-spam**
- Telegram bot that deletes only high-confidence spam: gh:backmeupplz/jev_antispam_bot
- Discord moderation bot "Soter": HN:49825787. mastra-jev-moderation (CodeAlive-AI)
- Trust and safety ideas (severity × confidence → allow/warn/review/block): https://docs.typesafe.ai/concepts/use-case-map.md

**Email, support, CRM**
- Chatwoot conversation priority/labels: `captain/conversation_classifier_service.rb` in chatwoot
- inbox-zero decision model: `utils/decision-model/typesafe.ts`
- Bryo AI email triage (Gemini slightly more accurate, 10–20× the cost): MarkTechPost launch article
- Jevmail 5-tray Gmail sorter (awesome-jev-typesafe)
- Support cost study: HN:49794787. CraftCX write-up: HN:49846104

**Logs, code, security**
- Grev/jgrep "thinking grep", 1M log lines for about $10: HN:49837132, gh:kyu1204/jgrep
- jev-semgrep with AND/OR/NOT and JA/EN: gh:uehaj/jev-semgrep. askgrep: gh:fajarhide/askgrep
- SOC alert triage and grouping: HN:49850990, https://evals.typesafe.ai/

**Bulk business labelling**
- Ad teardown, 724 ads for 9¢ (Matthew Berman via https://linas.substack.com/p/how-to-use-jev-ai)
- Resume vs. 6,245 YC companies for $0.37: https://flaviocopes.com/jev/
- IRS forms across 261 classes: kyotofin (https://gist.github.com/drillan/6916b16e8ea31a8ec36c8f59d6483150)
- Forum DB curation for backlinks: HN:49804096. Site SEO audit with 52 rules: gh:AgriciDaniel/jev-seo
- PDF classification and packet splitting: gh:jerryjliu/docjev
- CV screening with an editable policy: gh:gtaras7/typesafe-jev
- Litigation discovery, 3 checks per page: https://www.langchain.com/blog/building-prod-with-jev-and-langgraph

**Feeds**
- worldmonitor headline threat level: `shared/jev-classify.js`
- "Should AI Kill Us All?", headlines every 10 minutes: shouldaikillusall.com (gh:hellogumbo/should-ai-kill-us-all)
