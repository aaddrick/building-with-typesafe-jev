# Shape: Gates

**Use when** something must be allowed, blocked, reviewed, or escalated before it happens: agent tool calls, shell commands, commits, migrations, trades, refunds, content, agent "done" claims.

## The shape

```
proposed action + context → code rules: a known-bad pattern blocks here, and Jev never sees it
                          → one request: specific risk Nouls + a severity Score (+ category Choice)
                          → code policy: block if any serious flag, review if uncertain, else allow
                          → log the answers; re-route cached answers when the policy changes
```

```python
import re

from typesafe_sdk import Noul, NoulCriteria, Score, TypeSafeClient

POLICY = {"review": 0.35, "block": 0.70, "severity_block": 1.5}   # one place, reviewable
# Exact conditions whose miss cannot be undone. Jev cannot override these.
DENY = [re.compile(p) for p in (
    r"\brm\s+(-\S+\s+)+(/|~|\$HOME)/?\*?(\s|$)",             # rm -rf on / or home, incl. ~/ and /*
    r"\bgit\s+push\b.*(--force|-f)\b",                          # force push
    r"\b(mkfs|dd\s+if=)",                                        # overwrite a disk
    r"\bDROP\s+(TABLE|DATABASE)\b",
)]

def gate(client: TypeSafeClient, command: str, cwd: str) -> str:
    if any(p.search(command) for p in DENY):
        return "block"
    r = client.system_one(
        state={"command": command, "cwd": cwd},
        questions={
            "deletes_data": Noul(instructions="Does `command` delete or overwrite files or data?"),
            "exfiltrates": Noul(
                instructions="Does `command` send local files, secrets, or env vars to a remote host?",
                criteria=NoulCriteria(true="Uploads, posts, or pipes local content to a network destination",
                                      false="No local content leaves the machine"),
            ),
            "outside_cwd": Noul(instructions="Does `command` modify anything outside `cwd`?"),
            "severity": Score(
                instructions="If `command` went wrong, how bad would the damage be?",
                criteria=["Nothing lasting; trivially undone", "Recoverable with effort",
                          "Irreversible loss or exposure"],
            ),
        },
    )
    flags = [r.nouls[k].noul for k in ("deletes_data", "exfiltrates", "outside_cwd")]
    if max(flags) >= POLICY["block"] or r.scores["severity"].score >= POLICY["severity_block"]:
        return "block"
    if max(flags) >= POLICY["review"]:
        return "review"
    return "allow"
```

## Variants

- **Allow/ask/deny Choice**: one 3-way verdict. It is simpler, but you lose the reason and the ability to re-tune per flag.
- **Completion gate ("not done until Jev agrees")**: Stop hooks ask evidence questions ("were the tests run?", "does the diff match the stated change?") before an agent may finish.
- **Pre-action gate in finance**: Jev runs before a deterministic risk engine and before a slower LLM gate.
- **Verified cascade**: Jev checks a cheap LLM's output. Only flagged cases go to the expensive model (see `llm-pairing.md`).
- **Input and output batteries**: separate question sets for the user prompt and for the model's reply.
- **Window or burst gate** (Discord raid, fraud burst, alert storm): code computes the window stats (join rate, message rate, account ages, duplicate ratio) and samples 5–20 events into the state. Nouls ask "coordinated raid?" and "spam-bot pattern?", a Score rates severity, and the policy decides whether to lock, alert, or allow. Keep the rates and counts in code, because Jev does not count.
- **Human-in-the-loop UX**: return a Choice to the human as buttons ("Reverse Jev").

## Field lessons

- Combine flags with the **maximum**, never the average. One serious flag must win.
- Keep the policy (thresholds, precedence) in code or config. Re-running a policy on cached probabilities costs nothing.
- Phrase every flag so that yes = the bad thing. Write `true`/`false` criteria for subtle boundaries.
- Jev is not a security boundary against adversarial input. Keep untrusted text in its own field, add an injection Noul, and never let a Jev "allow" alone authorize money or deletion. Put exact rules in code before the Jev call: a denylist, a spending limit, a protected branch. A rule's block stands whatever Jev answers. Jev judges what the rules do not decide, and can only make the result stricter.
- Reported wins: approvals 8.7× faster and 4.4× fewer prompts on 153 real commands. Vercel's command-safety review was 5–18× faster than an OpenAI model.

## Prior art

**Agent tool and command gates**
- LangChain AutoModeMiddleware, a Noul blocks risky tool calls: [langchain.com](https://www.langchain.com/blog/building-a-harness-with-jev)
- hermes-jev-approvals, 8.7× faster, 4.4× fewer prompts: [anpicasso/hermes-jev-approvals](https://github.com/anpicasso/hermes-jev-approvals)
- jev-guard, three questions before every call (deny/ask/allow): [blacksinisterx/jev-guard](https://github.com/blacksinisterx/jev-guard)
- actionreflex: [eyenpi/actionreflex](https://github.com/eyenpi/actionreflex). pi-warden: [DevMortimer/pi-warden](https://github.com/DevMortimer/pi-warden)
- Agent Chaperone, tool calls + results + injection: [HN](https://news.ycombinator.com/item?id=49789538)
- Vercel command-safety classifier (Pranit Sharma): [techcrunch.com](https://techcrunch.com/2026/09/18/a-new-kind-of-ai-model-from-a-chatgpt-inventor-is-thrilling-developers/)
- OpenRouter cookbooks "Gate Agent Tool Calls" and "Auto-Approve Coding Agent Permission Prompts": [openrouter.ai](https://openrouter.ai/typesafe)
- Pydantic AI harmful-request example: [pydantic.dev](https://pydantic.dev/docs/ai/models/typesafe/)
- claude-code-templates jev-auto-mode security judge: [davila7/claude-code-templates](https://github.com/davila7/claude-code-templates)

**Completion and "done" gates**
- ralph-jev, the loop won't stop until the Jev judge agrees: [flaviomartil/ralph-jev](https://github.com/flaviomartil/ralph-jev)
- jev-belay (4 evidence questions): [valentynkit/jev-belay](https://github.com/valentynkit/jev-belay), limpet: [noplan-inc/limpet](https://github.com/noplan-inc/limpet)
- Overseer rubric for CLI agents (idea): [HN](https://news.ycombinator.com/item?id=49723571)

**Code and CI gates**
- Destructive migration blocker: [opaielsheikh/typesafe-migration-guard](https://github.com/opaielsheikh/typesafe-migration-guard)
- Commit message vs. diff + secrets: [valentynkit/jev-commit](https://github.com/valentynkit/jev-commit). Test claims: [allebee/pytest-jev](https://github.com/allebee/pytest-jev)
- Math-To-Manim stage approval: [`astra/jev.py`](https://github.com/HarleyCoops/Math-To-Manim/blob/main/astra/jev.py) in [HarleyCoops/Math-To-Manim](https://github.com/HarleyCoops/Math-To-Manim)

**Money and risk gates**
- Rust MT4 service behind a deterministic risk gate: [iamngoni/veyra](https://github.com/iamngoni/veyra)
- QuantDinger pre-trade gate: [gist.github.com](https://gist.github.com/drillan/6916b16e8ea31a8ec36c8f59d6483150)
- Refund branching at >85% confidence: [tomshardware.com](https://www.tomshardware.com/tech-industry/artificial-intelligence/typesafe-ais-jev-offers-an-alternative-to-llms-that-claims-to-be-193x-faster-and-445x-cheaper-system-one-type-model-is-bespoke-for-probabilistic-decision-making)
- Voice banking, confidence rising with the stakes: [docs.typesafe.ai](https://docs.typesafe.ai/patterns/confidence-routing.md)

**Content gates**
- LLM guardrails cookbook (strict/permissive policies): [docs.typesafe.ai](https://docs.typesafe.ai/cookbooks/llm_guardrails.md)
- deer-flow guardrails: [`backend/packages/harness/deerflow/guardrails/typesafe.py`](https://github.com/bytedance/deer-flow/blob/main/backend/packages/harness/deerflow/guardrails/typesafe.py) in [bytedance/deer-flow](https://github.com/bytedance/deer-flow), LiteLLM TypeSafe guardrail hook: [`litellm/proxy/guardrails/guardrail_hooks/typesafe/typesafe.py`](https://github.com/BerriAI/litellm/blob/main/litellm/proxy/guardrails/guardrail_hooks/typesafe/typesafe.py) in [BerriAI/litellm](https://github.com/BerriAI/litellm)
