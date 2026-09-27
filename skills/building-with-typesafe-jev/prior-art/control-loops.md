# Shape: Control Loops

**Use when** something must act repeatedly on changing state: games, simulations, robots, drones, vehicles, trading, device automation.

## The shape

```
loop every tick:
    observe  → code turns raw state into compact text/JSON (RAM, CV, order book, a11y tree)
    decide   → one request: a Choice over the LEGAL actions, plus speculative side questions
    act      → code executes: pathing, flight control, order placement, input injection
    verify   → code checks the effect; failures feed the next observation
```

Code owns physics, pathing, math, risk limits, and the action set. Jev only answers "what does this situation call for?".

```python
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

client = TypeSafeClient()  # one client for the whole loop

def decide(obs: dict, legal: list[str]) -> str | None:
    r = client.system_one(
        state={"observation": obs},
        questions={
            "action": Choice(
                instructions="Given `observation`, which action best advances the goal?",
                criteria={a: None for a in legal},     # only legal actions; rebuild every tick
            ),
            "danger": Score(
                instructions="How much immediate danger is the agent in?",
                criteria=["No threat nearby", "Threat present but not engaging",
                          "Taking damage or about to"],
            ),
            "target_lost": Noul(instructions="Is the tracked target no longer visible in `observation`?"),
        },
    )
    if r.choices["action"].confidence < 0.4:
        return None                                    # hold, or escalate to a planner
    return r.choices["action"].choice
```

## Variants

- **Hierarchical**: Jev picks a goal ("go to Pewter City"), code pathfinds (A*). Jev only takes the branch points. This is cheaper and more robust than per-button control.
- **Planner + actor**: an LLM sets a goal every N ticks, and Jev picks macro-actions each tick. See `llm-pairing.md`.
- **Objective ladder**: code keeps a fixed curriculum (wood → stone → iron → diamond). Jev picks among the actions for the current rung.
- **Tutor → student**: log Jev's decisions from successful episodes and train a small local policy that gradually takes over. The loop gets cheaper the longer it runs.
- **Multi-channel**: separate questions per subsystem (navigation vs. combat, direction vs. regime vs. inventory) in the same request.

## Field lessons

- Put **objects**, not pixels or raw bytes, in the state: object-centric JSON from RAM, numbered UI elements, a range-sector table from CV. Jev is text-only and weak on raw numbers.
- Keep what code observed apart from what Jev inferred. An inferred label is not a fact. Before acting on an answer, check that the state it came from still holds. A decision about a stale observation is a decision about a different situation.
- Rebuild the Choice options every tick from what is actually legal. An illegal option wastes probability mass and invites bad actions.
- Tick rates people hit: about 2.5 Hz (drone), about 5 Hz (4 questions every 200 ms, driving), about 10 Hz (Doom), about 300 ms per block (on-chain trading). Per-decision latency is about 80–300 ms.
- Search-heavy games (chess) fail. Reflex and situational games (Doom, Mario, Pong, Minecraft survival) work.
- For money, Jev proposes and a deterministic risk gate disposes. Nobody lets Jev place orders unguarded. Use dry-run defaults.
- Cost reference: Doom about $7/hour at 10 Hz. Minecraft about 1¢ per 2 minutes. Pokémon Red took 4 badges for under $0.50.

## Prior art

**Games**
- Doom from text state, about 10 Hz, about $7/hour: TypeSafe launch post [typesafe.ai](https://typesafe.ai/blog/introducing-system-one-models-and-jev). Kevin Madura's ViZDoom version, with separate navigation (5 decisions/s) and combat (12 decisions/s) channels: [mattpaige68.substack.com](https://mattpaige68.substack.com/p/a-new-ai-model-just-launched-that)
- Wikiracing: link Choice, with a Score pre-rank when there are more than 255 links (same launch post).
- StarCraft 1998 shareware, mouse/keyboard harness, beat mission 1 in 421 decisions: [phyous/tsai-sc](https://github.com/phyous/tsai-sc)
- StarCraft II "JEV-Star": [HN](https://news.ycombinator.com/item?id=49834465)
- Civilization II in a browser harness: [phyous/tsai-civ2](https://github.com/phyous/tsai-civ2)
- Super Mario Bros, RAM to object JSON, a Choice over 7 NES inputs: [fhshaik/typesafe-mario](https://github.com/fhshaik/typesafe-mario)
- Pokémon Red, goal Choice + A*, 4 badges for under $0.50: [milanboers/jev-plays-pokemon](https://github.com/milanboers/jev-plays-pokemon), [HN](https://news.ycombinator.com/item?id=49845172)
- Minecraft, Mineflayer, objective ladder, 5–30 legal actions per tick: [Anahadd/jev-minecraft](https://github.com/Anahadd/jev-minecraft). It learned to flee zombies unprompted: [mindstudio.ai](https://www.mindstudio.ai/blog/jev-system-one-model-launch)
- Minecraft dragon kill with an LLM + Jev pair: [rmalde/minecraft-agent](https://github.com/rmalde/minecraft-agent)
- Craftax, LLM planner + Jev macro-options, 5-agent comparison: [mansicer/jev-plays](https://github.com/mansicer/jev-plays)
- WoW TBC levelling, tutor → student distillation: [chalkychalk42/jev](https://github.com/chalkychalk42/jev)
- Clash Royale, card + placement: [vishxrad/clashroyale-jev](https://github.com/vishxrad/clashroyale-jev)
- Pong vs. LLMs: [runtimewire.com](https://runtimewire.com/article/diogo-almeida-typesafe-jev-40m-seed-pong)
- Snake and a fighting arena, Jev vs. the open Laya model: [PromptEngineer48/laya-vs-jev-arena](https://github.com/PromptEngineer48/laya-vs-jev-arena)
- Chess (failure case): [dperezcabrera/system-one-chess](https://github.com/dperezcabrera/system-one-chess), [HN](https://news.ycombinator.com/item?id=49746967)

**Robots, vehicles, simulations**
- Camera-only drone in MuJoCo, CV state → manoeuvre Choice + risk Score + "target lost" Noul at about 2.5 Hz: [RomanSlack/jev-drone](https://github.com/RomanSlack/jev-drone)
- Franka arm from plain-English goals: [TarunTomar122/jev-askable-arm](https://github.com/TarunTomar122/jev-askable-arm)
- MuJoCo robot workbench, Jev vs. MiniCPM: [FBddcz/embodied-jev](https://github.com/FBddcz/embodied-jev)
- Three.js driving from path, traffic, and signal tables: [standardagents/jevpilot](https://github.com/standardagents/jevpilot). A 2D browser car sim that asks 4 questions every 200 ms: [vinilana/live-jev](https://github.com/vinilana/live-jev)
- Four-camera car with radar and blind-spot inputs: [kavehmz/typesafe-playground](https://github.com/kavehmz/typesafe-playground)
- Citywide traffic signal policy (Chicago): [skcache/jevtrafficsim](https://github.com/skcache/jevtrafficsim)
- Air traffic approach control: [HN](https://news.ycombinator.com/item?id=49829999)
- Rain nowcasting from radar vectors (App Store): [HN](https://news.ycombinator.com/item?id=49847565)

**Markets**
- On-chain market maker, one decision per Monad block, post-only orders: [jarrodwatts/jev-trader](https://github.com/jarrodwatts/jev-trader)
- Hyperliquid, five sleeves, long/short then open/close/hold: [aowang-ai/jev-trade](https://github.com/aowang-ai/jev-trade)
- Six-judgment microstructure policy (regime, direction, toxic flow, liquidity stress, quote environment, inventory): [buberlo/jev-trader](https://github.com/buberlo/jev-trader)
- Self-rewriting Binance bot. Qwen rewrites the rules every 30 minutes, champion vs. challenger: [learnwithmeai.com](https://www.learnwithmeai.com/p/jev-trading-bot)
- Polymarket 5-minute BTC UP/DOWN/abstain: [VGabriel45/polymarket-btc5m-jev-trading](https://github.com/VGabriel45/polymarket-btc5m-jev-trading)
- O'Neil momentum backtest. Code owns stops and risk: [michaelpersonal/jev-trade-cc](https://github.com/michaelpersonal/jev-trade-cc)
- Survey of finance projects: [gist.github.com](https://gist.github.com/drillan/6916b16e8ea31a8ec36c8f59d6483150)

**Devices**
- Android over ADB, observe → decide → act → verify: [Friedjof/jev-mobile](https://github.com/Friedjof/jev-mobile). For computer and browser loops, see `select-from-candidates.md`.
