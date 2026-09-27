# Shape: Select From Candidates

**Use when** the answer already exists somewhere: a UI element, a tool, a function argument value, a span of text, a model tier, a handler. Jev picks it and code copies it. Jev never generates.

## The shape

```
enumerate  → code lists candidates (DOM/a11y refs, OCR boxes, regex hits, tool registry, Literal values)
select     → Choice with the candidates as keys (+ "none"), plus an absolute Noul ("does any fit?")
execute    → code uses the exact selected string or object
```

```python
from typesafe_sdk import Choice, Noul, TypeSafeClient

def pick(client: TypeSafeClient, goal: str, elements: list[dict]) -> dict | None:
    table = {f"e{i}": el for i, el in enumerate(elements)}       # opaque keys, details in state
    r = client.system_one(
        state={"goal": goal, "elements": table},
        questions={
            "target": Choice(
                instructions="Which element in `elements` should be used next to achieve `goal`?",
                criteria={k: None for k in table} | {"none": "No element helps with the goal"},
            ),
            "destructive": Noul(instructions="Would acting on the most relevant element delete, "
                                             "pay, send, or otherwise be hard to undo?"),
        },
    )
    t = r.choices["target"]
    if t.choice == "none" or t.confidence < 0.5 or r.nouls["destructive"].noul > 0.5:
        return None                                              # ask a human or escalate
    return table[t.choice]
```

## Variants

- **Operation + target in one Choice**: keys like `click:e12`, `type:e4`, `scroll:down`. One call per step.
- **Function calling with no LLM**: a `__tool__` Choice picks the function. Each `Literal` argument becomes a Choice keyed by the exact accepted strings, each `list[Literal]` one Noul per member, each `bool` a Noul. A `stated` Noul per argument ("did the user say anything about this?") keeps defaults. Code builds any text reply. Put all questions in one request (54 in the cookbook).
- **Value extraction**: an over-eager regex finds candidates. The candidate strings are the Choice keys, plus `none`. No transposed digits, no invented values.
- **Routers**: the candidates are models, effort levels, skills, MCP tools, or HTTP handlers.
- **Large rosters**: up to 255 options per Choice. Above that, pre-rank with a Score or Noul, or use two stages (short descriptions → top 3 with full text).

## Field lessons

- Give opaque keys (`e0`, `c3`) and put the details in state or in the option values. Where the exact string is the payload (extraction, `Literal` args), use the string itself as the key.
- A Choice always has a winner. Pair it with an absolute Noul (`exists`, `fits`, `stated`), or add a `none` key.
- Numbered element tables beat screenshots: $0.0002–$0.004 per step and 7 s flight bookings, against minutes and dollars for vision agents.
- When a free-text value is needed (a search query, a message body), call a small LLM for that one field only.
- A distilled 706k-parameter specialist beat hosted Jev on form filling (99.7% vs. 83.6%, 7–9 ms). At high volume on one narrow task, consider distilling.

## Prior art

**Browser, computer, phone**
- Browser Use "jev-ultrafast": a numbered element table, one Choice = operation + target. Zürich→London flight search in 7.1 s for $0.0039 (via [dev.to](https://dev.to/valyuai/how-to-use-jev-a-practical-guide-to-typesafes-system-one-model-g5e))
- Browserbase Stagehand `act()` rebuilt on Jev, median 1.97 s → 0.46 s: [langchain.com](https://www.langchain.com/blog/building-prod-with-jev-and-langgraph)
- Mac computer use with OCR, no screenshots, about $0.0002 per step, an LLM only for free text: [awlevin/typesafe-computer-use](https://github.com/awlevin/typesafe-computer-use)
- Accessibility-tree browser agent, 10–40 refs per step, 21–23 decisions all correct for about $0.001: [HN](https://news.ycombinator.com/item?id=49758669)
- macOS Accessibility tree, with voice control: [savka777/jev-use](https://github.com/savka777/jev-use). CUA's separate Jev example: [trycua/cua](https://github.com/trycua/cua) `libs/cua-driver/examples/jev-use`
- Droidrun mobile-jev, 9 Uber actions on a real phone in 21 s: [droidrun/mobile-jev](https://github.com/droidrun/mobile-jev). iOS/Android jev-phone: [HN](https://news.ycombinator.com/item?id=49831841)
- Rental search across Craigslist, FB Marketplace, Redfin, Zillow: Hearth, [Nancy-Chauhan/hearth-jev-rental-search](https://github.com/Nancy-Chauhan/hearth-jev-rental-search)
- Distilled form-filler that beats Jev: [HN](https://news.ycombinator.com/item?id=49767564)

**Tool and function calling without an LLM**
- Function-calling cookbook: [docs.typesafe.ai](https://docs.typesafe.ai/cookbooks/function_calling.md)
- Chat where Jev picks the tool and arguments and code builds the reply: [w3cj/jev-chat](https://github.com/w3cj/jev-chat)
- WebMCP browser extension: [sdras/jev-webmcp-extension](https://github.com/sdras/jev-webmcp-extension)
- jevexpress: Express with no routes, Jev picks the handler: [carllippert/jev-router](https://github.com/carllippert/jev-router)
- Smart-home demo, speculative fan-out over category/room/device/action: [docs.typesafe.ai](https://docs.typesafe.ai/demos/smart-home.md)

**Extraction by selection**
- Pre-parsed value extraction cookbook: [docs.typesafe.ai](https://docs.typesafe.ai/cookbooks/pre_parsed_value_extraction_cookbook.md)
- Date extraction as 7 enumerated Choices: [docs.typesafe.ai](https://docs.typesafe.ai/cookbooks/date_extraction_cookbook.md)
- Line-by-line search, a Choice over line IDs + an `exists` Noul: [docs.typesafe.ai](https://docs.typesafe.ai/cookbooks/semantic_find.md)

**Routers**
- OpenRouter official "Jev Router" (model + reasoning effort): [openrouter.ai](https://openrouter.ai/typesafe)
- LangChain model-routing middleware: [langchain.com](https://www.langchain.com/blog/building-a-harness-with-jev)
- [jev-router](https://github.com/gargpratyush/jev-router), [jev-codex-router](https://github.com/0xNatoshi/jev-codex-router), [pi-jev-model-router](https://github.com/da-vinci-noob/pi-jev-model-router), [tiershift](https://github.com/iamvatsalpatel/tiershift)
- Skill routers: skill_suggestion cookbook [docs.typesafe.ai](https://docs.typesafe.ai/cookbooks/skill_suggestion.md), [jev-skill-suggester](https://github.com/win4r/jev-skill-suggester), [typesafe-skill-router](https://github.com/DECRUX9812/typesafe-skill-router), [skillranker](https://github.com/Dicklesworthstone/skillranker), [tink-route](https://github.com/jon-devlapaz/tink-route)
- Jev-pilot, Claude Code effort/model/skill per prompt: [HN](https://news.ycombinator.com/item?id=49837537)
- OpenCode agent router for subagents: [HN](https://news.ycombinator.com/item?id=49822796)
