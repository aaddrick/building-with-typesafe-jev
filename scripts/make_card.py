#!/usr/bin/env python3
"""Draw the hero card at .github/assets/hero.png.

The card is the skill's argument in one picture. The left panel is the old way:
an LLM with Structured Outputs returns valid JSON, but a field is wrong and its
confidence is generated, not calibrated. The right panel is the Jev way: three
typed answers, one per primitive, each with the probability your code branches on.

Run it after any change to the header text, the example, or the harness list:

    python3 scripts/make_card.py

Needs Pillow and NumPy. Neither is a test dependency, so CI does not run this.
Pillow encodes the same pixels differently across versions, so no gate checks
the committed PNG against a fresh render. Regenerate by hand and commit it.

Fonts live in assets/fonts/. Both families are OFL; the licenses sit beside them.
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "assets" / "fonts"
# Every string on the card, per variant. A variant without its own "prose"
# or "rows" uses the English panel content.
VARIANTS = {
    "en": {
        "out": ROOT / ".github" / "assets" / "hero.png",
        "tag1": "Typed decisions with calibrated confidence, for your coding agent.",
        "tag2": "Prior art from 150+ community projects, sorted by shape.",
        "left": "LLM  +  STRUCTURED OUTPUTS",
        "right": "JEV  ·  ONE CALL  ·  100-200 MS",
        # Schema-valid JSON is not a right answer, and the confidence field
        # is generated like any other token.
        "prose": [
            "{",
            "  \"department\": \"billing\",",
            "  \"severity\": \"medium\",",
            "  \"refund\": false,",
            "  \"confidence\": 0.95",
            "}",
            "",
            "// valid JSON on every call",
            "// confidence: generated, not calibrated",
        ],
        "fade": False,
        "wrong": 3,
        "dim_from": 7,
    },
}
args = [a for a in sys.argv[1:]]
variant = "en"
if "--variant" in args:
    i = args.index("--variant"); variant = args[i + 1]; del args[i:i + 2]
V = VARIANTS[variant]

S = 2                      # supersample factor, resized down at the end
W, H = 1280 * S, 640 * S   # GitHub's social preview size

# --- palette ---------------------------------------------------------------
BOARD      = (0x1C, 0x1F, 0x24)
BOARD_DARK = (0x12, 0x14, 0x17)
PANEL_OLD  = (0xE6, 0xDF, 0xD2)   # prose: warm paper
PANEL_NEW  = (0xF3, 0xF1, 0xEA)   # typed: clean paper
INK        = (0x1B, 0x19, 0x16)
INK_MUTE   = (0x8A, 0x85, 0x7A)
RULE       = (0xC9, 0xC2, 0xB3)
RED        = (0xA8, 0x37, 0x2A)
AMBER      = (0xD9, 0x8B, 0x0B)   # the accent: the number code branches on
TRACK      = (0xDD, 0xD7, 0xCA)
GREY_TEXT  = (0x9A, 0x9E, 0xA6)


def disp(size, weight="Bold"):
    return ImageFont.truetype(str(FONTS / f"SairaCondensed-{weight}.ttf"), int(size * S))


def mono(size, weight="Regular"):
    return ImageFont.truetype(str(FONTS / f"IBMPlexMono-{weight}.ttf"), int(size * S))


def tracked(draw, xy, text, font, fill, track=0):
    """Draw text with letter spacing. Returns the end x."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + track * S
    return x


def tracked_len(draw, text, font, track=0):
    return sum(draw.textlength(c, font=font) + track * S for c in text)


img = Image.new("RGB", (W, H), BOARD)
d = ImageDraw.Draw(img)
for y in range(0, H, 4 * S):
    d.line([(0, y), (W, y)], fill=(BOARD[0] + 3, BOARD[1] + 3, BOARD[2] + 3), width=1)
d.rectangle([0, 0, W, 10 * S], fill=BOARD_DARK)
d.rectangle([0, H - 10 * S, W, H], fill=BOARD_DARK)

# --- header: both tagline lines, verbatim from README.md -------------------
PAD = 64 * S
tracked(d, (PAD, 44 * S), "BUILDING WITH TYPESAFE JEV", disp(56), PANEL_NEW, track=1.5)
d.text((PAD, 108 * S), V["tag1"],
       font=disp(29, "Medium"), fill=GREY_TEXT)
d.text((PAD, 143 * S), V["tag2"],
       font=disp(26, "Medium"), fill=AMBER)


def panel(x, y, w, h, paper, tilt, seed):
    """Paper panel with a soft shadow, slight tilt, faint grain."""
    pad = 26 * S
    lay = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rectangle([pad, pad, pad + w, pad + h], fill=paper + (255,))
    a = np.array(lay).astype(np.int16)
    noise = np.random.default_rng(seed).integers(-4, 5, (lay.size[1], lay.size[0], 1))
    mask = a[:, :, 3] > 0
    a[:, :, :3] = np.clip(a[:, :, :3] + noise * mask[:, :, None], 0, 255)
    lay = Image.fromarray(a.astype(np.uint8))
    sh = Image.new("RGBA", lay.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([pad, pad, pad + w, pad + h], fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(9 * S)).rotate(tilt, resample=Image.BICUBIC)
    lay = lay.rotate(tilt, resample=Image.BICUBIC)
    img.paste(sh, (x - pad, y - pad + 5 * S), sh)
    img.paste(lay, (x - pad, y - pad), lay)
    return ImageDraw.Draw(img)


PY, PH = 200 * S, 336 * S
GAP = 36 * S
LW = 440 * S
RX, RW = PAD + LW + GAP, W - PAD * 2 - LW - GAP

# ===========================================================================
# Left: LLM prose where code wanted a value
# ===========================================================================
d = panel(PAD, PY, LW, PH, PANEL_OLD, 0.4, 3)
tracked(d, (PAD + 24 * S, PY + 18 * S), V["left"], disp(17, "SemiBold"), INK_MUTE, track=2)
cx, cy, r = PAD + LW - 40 * S, PY + 30 * S, 11 * S
d.line([(cx - r, cy - r), (cx + r, cy + r)], fill=RED, width=4 * S)
d.line([(cx - r, cy + r), (cx + r, cy - r)], fill=RED, width=4 * S)

prose = V.get("prose") or [
    "Sure! Here is the JSON you asked",
    "for. Based on the ticket, it seems",
    "like the department could be",
    "\"billing\" (or possibly technical?),",
    "with a severity of around medium,",
    "and the customer might want a",
    "refund, although it is hard to say",
    "for certain without more context.",
    "```json { \"department\": \"billi",
]
ty = PY + 58 * S
for i, line in enumerate(prose):
    if i == V.get("wrong"):
        color = RED
    elif i < V.get("dim_from", 3):
        color = (0x5E, 0x5A, 0x52)
    else:
        color = INK_MUTE
    d.text((PAD + 24 * S, ty), line, font=mono(17), fill=color)
    ty += 29 * S
fade = Image.new("RGBA", (LW, 90 * S), (0, 0, 0, 0))
fd = ImageDraw.Draw(fade)
for i in range(90 * S):
    fd.line([(0, i), (LW, i)], fill=PANEL_OLD + (int(255 * i / (90 * S)),))
if V.get("fade", True):
    img.paste(fade, (PAD, PY + PH - 90 * S), fade)
d = ImageDraw.Draw(img)

# ===========================================================================
# Right: three typed answers, one per primitive
# ===========================================================================
d = panel(RX, PY, RW, PH, PANEL_NEW, -0.3, 5)
tracked(d, (RX + 24 * S, PY + 18 * S), V["right"], disp(17, "SemiBold"), INK_MUTE, track=2)

rows = V.get("rows") or [
    ("CHOICE", "department", "billing", 0.92, "confidence 0.88"),
    ("SCORE",  "severity",   "1.43 / 2", 0.715, "scale 0-2"),
    ("NOUL",   "refund",     "0.99",    0.99, "P(yes)"),
]
row_h = (PH - 60 * S) // 3
lab_f, key_f, val_f, note_f = disp(18, "SemiBold"), mono(18), mono(24, "Medium"), mono(15)
for i, (prim, key, val, frac, note) in enumerate(rows):
    ry = PY + 56 * S + i * row_h
    if i:
        d.line([(RX + 20 * S, ry - 8 * S), (RX + RW - 20 * S, ry - 8 * S)], fill=RULE, width=2 * S)
    tracked(d, (RX + 24 * S, ry + 6 * S), prim, lab_f, (0x5E, 0x6B, 0x66), track=2.5)
    d.text((RX + 130 * S, ry + 4 * S), key, font=key_f, fill=INK_MUTE)
    d.text((RX + 300 * S, ry), val, font=val_f, fill=INK)
    d.text((RX + RW - 24 * S - d.textlength(note, font=note_f), ry + 7 * S), note, font=note_f, fill=INK_MUTE)
    bx0, bx1, by = RX + 130 * S, RX + RW - 24 * S, ry + 46 * S
    d.rounded_rectangle([bx0, by, bx1, by + 12 * S], radius=6 * S, fill=TRACK)
    d.rounded_rectangle([bx0, by, bx0 + int((bx1 - bx0) * frac), by + 12 * S], radius=6 * S, fill=AMBER)

# --- footer ----------------------------------------------------------------
BASE = H - 38 * S
url_font = mono(20, "Medium")
d.text((PAD, BASE - url_font.getmetrics()[0]), "github.com/aaddrick/building-with-typesafe-jev",
       font=url_font, fill=(0x8E, 0x93, 0x9B))
harnesses = "UNOFFICIAL  ·  CLAUDE CODE  ·  CODEX  ·  ANTIGRAVITY CLI"
hf = disp(18, "SemiBold")
tracked(d, (W - PAD - tracked_len(d, harnesses, hf, track=2), BASE - hf.getmetrics()[0]),
        harnesses, hf, (0x6E, 0x73, 0x7B), track=2)

out_path = Path(args[0]) if args else V["out"]
out = img.resize((W // S, H // S), Image.LANCZOS)
out.save(out_path, optimize=True)
print(f"wrote {out_path} {out.size[0]}x{out.size[1]}")
