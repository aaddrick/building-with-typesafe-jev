# Shape: Pairing Jev With an LLM

**Use when** part of the job needs generation, long reasoning, or perception, and part is a frequent, fast judgment. Split them.

## The shapes

| Pairing | Who does what | Use for |
|---|---|---|
| **Planner / actor** | An LLM sets a goal every N steps. Jev picks actions every step. | Games, robots, long-horizon agents |
| **Verify-then-escalate cascade** | A cheap LLM produces. Jev checks each field or claim. Flagged items go to a strong LLM. | Extraction, answers, citations |
| **Front-door router** | Jev classifies intent and complexity. It routes to code, a specialist LLM, or a human. | Support, assistants |
| **Proposer / selector** | An LLM or CV proposes candidates. Jev selects. | Extraction, detection boxes, art |
| **Jev decides, LLM writes** | Jev picks the tool, arguments, and branch. A small LLM writes only the free-text field. | Tool calling, replies |
| **Rule writer / runner** | An LLM rewrites the rules or questions offline. Jev runs them live. | Trading bots, prompt → rubric migration |
| **Tutor → student** | Jev's decisions train a small local model that takes over | High-volume narrow loops |
| **Trigger → investigator** | Jev decides "is this serious?". An LLM digs into logs and writes a report. | Monitoring, SOC |

```python
from typesafe_sdk import Noul, TypeSafeClient

FIRE = 0.7
FLAWS = {
    "hallucinated": "Is `extracted_value` absent from `source_text`?",
    "off_target": "Does `extracted_value` answer a different field than `field_spec` asks for?",
    "format_violation": "Does `extracted_value` break the format in `field_spec`?",
}

def verify(client: TypeSafeClient, source: str, schema: dict, record: dict) -> bool:
    qs = {
        f"{field}::{flaw}": Noul(instructions={
            "field_spec": schema[field], "extracted_value": value, "question": text})
        for field, value in record.items() for flaw, text in FLAWS.items()
    }
    r = client.system_one(state={"source_text": source}, questions=qs)
    return max(a.noul for a in r.nouls.values()) > FIRE      # True → escalate to the strong LLM
```

## Field lessons

- Escalate on the **maximum** flag, not the average.
- Hallucination checks read literally. A reformatted value ("03/14/2026" against the source's "March 14, 2026") scored 0.84 "absent" in a live test. Normalize values before the check, or ask "Is the value in `extracted_value` stated in `source_text`, in any format?".
- Put Jev on the hot path (every tick, every item) and the LLM on the cold path (rare, hard).
- The route "define in Claude → run in Jev → train your own classifier on the collected labels" came up repeatedly. Jev is a middle stage, not always the end state.
- An LLM ensemble can generate labels when you have none, for tuning thresholds or training a downstream model.

## Prior art

- SDE cascade cookbook (gpt-5.4-mini extracts → Jev checks per field → gpt-5.5 escalates): [docs.typesafe.ai](https://docs.typesafe.ai/cookbooks/sde_cascade.md)
- OpenRouter "Cut LLM Cost with a Jev-Verified Cascade": [openrouter.ai](https://openrouter.ai/typesafe)
- Cheap-confirm-escalate (regex/small model → Jev → big model): [HN](https://news.ycombinator.com/item?id=49763623). Lev: [HN](https://news.ycombinator.com/item?id=49844757)
- LangGraph Jev + LLM fallback: [langchain.com](https://www.langchain.com/blog/building-prod-with-jev-and-langgraph)
- Intent routing pattern (code / specialist LLM / human): [docs.typesafe.ai](https://docs.typesafe.ai/patterns/intent-routing.md)
- Smart home: Jev fan-out, a compound-request Noul → an LLM splits the request, chat falls back to an LLM: [docs.typesafe.ai](https://docs.typesafe.ai/demos/smart-home.md)
- Craftax planner/actor with a 5-agent comparison: [mansicer/jev-plays](https://github.com/mansicer/jev-plays)
- Minecraft dragon kill (LLM + Jev): [rmalde/minecraft-agent](https://github.com/rmalde/minecraft-agent)
- Pokémon: Jev in the overworld, escalate hard battles to Sonnet/Opus (idea): [HN](https://news.ycombinator.com/item?id=49849494)
- Self-rewriting Binance bot (Qwen rewrites the rules every 30 minutes): [learnwithmeai.com](https://www.learnwithmeai.com/p/jev-trading-bot)
- WoW tutor → student distillation: [chalkychalk42/jev](https://github.com/chalkychalk42/jev)
- Pixel art (LLM sketches shapes → Jev picks style → code renders): [joce-unity/pixeljev](https://github.com/joce-unity/pixeljev)
- YOLO-World proposes boxes, Jev keeps or drops each: [huggingface.co](https://huggingface.co/spaces/iluvblender/yolo-jev-scene-filter)
- Fraud detection with Jev + Kimi K3: [x.com/nutlope](https://x.com/nutlope/status/2100614659690713543)
- Monitoring trigger → LLM report: [tomshardware.com](https://www.tomshardware.com/tech-industry/artificial-intelligence/typesafe-ais-jev-offers-an-alternative-to-llms-that-claims-to-be-193x-faster-and-445x-cheaper-system-one-type-model-is-bespoke-for-probabilistic-decision-making)
- Define in Claude, run in Jev: [HN](https://news.ycombinator.com/item?id=49719902). Prompt → rubric → own classifier: [HN](https://news.ycombinator.com/item?id=49849617)
- Jevper, Jev's interface on any OpenAI-compatible model: [HN](https://news.ycombinator.com/item?id=49815066). TypeSafe [`system-one-adapter-python`](https://github.com/typesafe-ai/system-one-adapter-python)
