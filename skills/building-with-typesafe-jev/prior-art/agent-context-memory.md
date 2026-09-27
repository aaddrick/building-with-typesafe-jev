# Shape: Agent Context, Memory, and Effort

**Use when** you are building harness plumbing for an LLM agent: what stays in context, what gets remembered, when memories expire, how much reasoning effort to spend, which skill or tool to surface.

## The shape

Replace generative steps (summarize, rewrite) with **per-item decisions**. The kept content stays verbatim.

```
compaction : for each context block → Choice keep / truncate / drop, given the current task
memory     : after each turn → Noul "anything worth remembering?" → Choice category → append verbatim
lease      : for each stored memory → Noul "does the new evidence invalidate this?"
effort     : each step → Score "how stuck / how hard is this step?" → map to reasoning effort or model tier
```

```python
from typesafe_sdk import Choice, TypeSafeClient

def compact(client: TypeSafeClient, task: str, blocks: list[str]) -> list[str]:
    qs = {
        f"b{i}": Choice(
            instructions={"question": "What should happen to `blocks[%d]` for the rest of `task`?" % i},
            criteria={"keep": "Still needed verbatim to finish the task",
                      "truncate": "Only the first lines or the result matter now",
                      "drop": "No longer relevant to the task"},
        )
        for i in range(len(blocks))
    }
    r = client.system_one(state={"task": task, "blocks": blocks}, questions=qs)
    out = []
    for i, b in enumerate(blocks):
        a = r.choices[f"b{i}"]
        if a.choice == "keep" or a.confidence < 0.5:           # unsure → keep
            out.append(b)
        elif a.choice == "truncate":
            out.append(b[:400] + "\n[truncated]")
    return out
```

Mind the 32k-token limit on state plus the longest question. Chunk the blocks across requests for long transcripts.

## Field lessons

- A verbatim keep/drop is safer than a summary: nothing gets paraphrased wrong, and the decision is auditable.
- Changing the model or effort mid-session can invalidate the prompt/KV cache and erase the savings. Keep the tier stable within a cacheable span ([HN](https://news.ycombinator.com/item?id=49831615)).
- Memory gates hit 98.5% save/skip accuracy at 0.3 s per decision.
- The effort governor reported about a 50% cost cut with the cache preserved.
- Default to keep, or to "remember nothing", when confidence is low. False drops hurt more than extra tokens.

## Prior art

**Compaction and pruning**
- fast-jev-compaction: [tamaratran/fast-jev-compaction](https://github.com/tamaratran/fast-jev-compaction). jev-pruner: [tamaratran/jev-pruner](https://github.com/tamaratran/jev-pruner). winnow: [GhalebDweikat/winnow](https://github.com/GhalebDweikat/winnow). save-token-jev: [IAmUnbounded/save-token-jev-clean](https://github.com/IAmUnbounded/save-token-jev-clean). fast-jev-compaction was announced on X as "Instant compaction for Claude" (@tamarajtran).
- LiteLLM TypeSafe guardrail that prunes tool results: `guardrail_hooks/typesafe/typesafe.py` in [BerriAI/litellm](https://github.com/BerriAI/litellm/blob/main/litellm/proxy/guardrails/guardrail_hooks/typesafe/typesafe.py)
- Context management "do all these tokens need to reach the agent?" (TypeSafe staffer idea): [HN](https://news.ycombinator.com/item?id=49719368)

**Memory**
- Jevmem, save/skip into JEVMEM.md after each message: [HN](https://news.ycombinator.com/item?id=49846413)
- Proactive memory formation and retrieval (idea): [HN](https://news.ycombinator.com/item?id=49721409)
- invalidate, memory leases ended by new evidence: [chopratejas/invalidate](https://github.com/chopratejas/invalidate)
- Jev-Mem, a paper using Jev as the memory control plane (typing, relations, routing), 0.777 LoCoMo: [libingzheren/Jev-Mem](https://github.com/libingzheren/Jev-Mem)

**Effort, model, and skill control**
- Vechen reasoning-effort governor, about 50% cost cut: [linas.substack.com](https://linas.substack.com/p/how-to-use-jev-ai)
- Jev-pilot (effort/model/skill per prompt): [HN](https://news.ycombinator.com/item?id=49837537). jev-effort: [HN](https://news.ycombinator.com/item?id=49824915)
- Skill suggestion cookbook (progressive disclosure over 182 skills): [docs.typesafe.ai](https://docs.typesafe.ai/cookbooks/skill_suggestion.md)
- Routers: see `select-from-candidates.md`

**Harness frameworks**
- Sokit, System One Harness, jevlike, DSPy fork: [HN](https://news.ycombinator.com/item?id=49744527), [HN](https://news.ycombinator.com/item?id=49778358), [HN](https://news.ycombinator.com/item?id=49719285)
- LangChain harness post (middleware for routing and auto mode): [langchain.com](https://www.langchain.com/blog/building-a-harness-with-jev)
- Jevify skill, converts an LLM "return JSON" call to Jev: [HN](https://news.ycombinator.com/item?id=49812519)
- Reverse Jev, the agent ends its turn with a Choice so the human replies with one button: [HN](https://news.ycombinator.com/item?id=49807602)
