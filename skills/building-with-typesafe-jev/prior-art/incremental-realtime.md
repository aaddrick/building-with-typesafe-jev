# Shape: Incremental and Real-Time Decisions

**Use when** the input arrives in pieces and you must decide before it is complete: speech transcripts, keystrokes, video captions, sensor feeds, live translation.

## The shape

```
on each increment (word, keystroke batch, caption segment):
    one request over the input so far: "is it complete enough?", "what is it?", "is it risky?"
    commit when confidence crosses a bar, or when a max hold time expires; otherwise wait
```

```python
from typesafe_sdk import Choice, Noul, TypeSafeClient

COMMIT_AT = 0.85
MAX_HOLD_S = 17.0

def on_partial(client: TypeSafeClient, text_so_far: str, held_for_s: float, intents: dict) -> str | None:
    r = client.system_one(
        state={"utterance_so_far": text_so_far},
        questions={
            "complete": Noul(instructions="Is `utterance_so_far` a complete thought that can be acted on now?"),
            "addressed_to_me": Noul(instructions="Is `utterance_so_far` addressed to the assistant?"),
            "intent": Choice(instructions="What does the speaker want?", criteria=intents | {"unclear": None}),
            "destructive": Noul(instructions="Would acting on `utterance_so_far` be hard to undo?"),
        },
    )
    ready = r.nouls["complete"].noul > 0.8 and r.choices["intent"].confidence >= COMMIT_AT
    if (ready or held_for_s > MAX_HOLD_S) and r.nouls["addressed_to_me"].noul > 0.7:
        if r.nouls["destructive"].noul > 0.5:
            return "confirm:" + r.choices["intent"].choice
        return r.choices["intent"].choice
    return None
```

## Field lessons

- Latency per decision is about 100–350 ms, fast enough to re-ask on every word or every 350 ms of typing.
- Always add a max-hold timeout. A dubbing app capped the hold at 17 s where an LLM approach needed 40 s.
- Ask "addressed to me?" and "destructive?" on every increment for voice. Partial speech misfires.
- Show the live probabilities in the UI (seek-bar painting, a morphing card, a top-3 bar). It makes the uncertainty legible and fun.
- Cost is small even at high frequency: dubbing runs about 2¢ per hour of audio.

## Prior art

- Real-time dubbing on iPhone ("is this translated sentence complete enough to speak?"), about 0.35 s, about 2¢/hour: [HN](https://news.ycombinator.com/item?id=49814743), [HN](https://news.ycombinator.com/item?id=49814753)
- Voice browser, about 12 questions per spoken word including destructive and addressed-to-me: [moritzkremb/jev-voice-browser](https://github.com/moritzkremb/jev-voice-browser)
- Voice-controlled Mac computer use: [X](https://x.com/instantricecook/status/2100814590300889426)
- Component Charades, Choice re-ranked every 350 ms while typing, commits at 0.85: [southleft/component-charades](https://github.com/southleft/component-charades)
- Shapeshift, one text box that morphs into an event card, checklist, or bill splitter, 14 questions per keystroke batch: [anishfn/shapeshift](https://github.com/anishfn/shapeshift)
- Steve Krouse's typewriter, 16 live Nouls as you type: [typesafe-demo.val.run](https://typesafe-demo.val.run/)
- YouTube sponsor skip painting the probability on the seek bar: [valentynkit/jev-skip](https://github.com/valentynkit/jev-skip). Podcast ad removal: [ttlequals0/MinusPodJev](https://github.com/ttlequals0/MinusPodJev) ([flaviocopes.com](https://flaviocopes.com/jev/))
- Real-time audio beeper with ffmpeg: [santos-sanz/jev-audio-beeper](https://github.com/santos-sanz/jev-audio-beeper)
- Speech-driven NPC addressee detection: [wondertwins/jev-benchmark](https://github.com/wondertwins/jev-benchmark)
- Home Assistant voice ("cold and dark in here" → lights and heat): [HN](https://news.ycombinator.com/item?id=49851245), [AboveColin/HA-Jev](https://github.com/AboveColin/HA-Jev)
- Home network monitoring in real time (the author's early experiment, mentioned in a RuntimeWire article on TypeSafe's valuation): [runtimewire.com](https://runtimewire.com/article/typesafe-investors-discuss-a-higher-valuation-after-jev-reaches-nearly-13-of-one)
- AI video editor, cutting >30 s tool latency (idea): [HN](https://news.ycombinator.com/item?id=49721095)
- For fixed-rate control loops, see `control-loops.md`
