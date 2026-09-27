#!/usr/bin/env python3
"""Annotate the API key walkthrough screenshots for the README.

The raw captures hold a live API key and account details, so they never enter
the repo. Capture them yourself (1512x807, console.typesafe.ai), then run:

    python3 scripts/annotate_screens.py /path/to/raw-dir

Expected raw files: 01-home.jpg, 02-keys.jpg, 03-name.jpg, 04-created.jpg.
Writes .github/assets/api-key/step-1.png ... step-4.png.

Every image gets the same treatment: blur the account name and every existing
key row, mask the new key's value, then draw an amber highlight box, a numbered
badge, and an arrow with a label on the one control the step is about.
Coordinates are in the 1512x807 capture frame.
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "assets" / "fonts"
OUT = ROOT / ".github" / "assets" / "api-key"

AMBER = (0xD9, 0x8B, 0x0B)
INK = (0x1B, 0x19, 0x16)
WHITE = (0xFF, 0xFF, 0xFF)

ACCOUNT = (0, 740, 265, 807)            # avatar, name, org
ROWS = (298, 162, 1480, 436)            # every key row: names, prefixes, creator


def font(size, weight="SemiBold"):
    return ImageFont.truetype(str(FONTS / f"SairaCondensed-{weight}.ttf"), size)


def blur(img, box, radius=14):
    region = img.crop(box).filter(ImageFilter.GaussianBlur(radius))
    img.paste(region, box[:2])


def mask_key(img, box):
    d = ImageDraw.Draw(img)
    d.rectangle(box, fill=(0xF4, 0xF4, 0xF2), outline=(0xE2, 0xE2, 0xDE))
    mono = ImageFont.truetype(str(FONTS / "IBMPlexMono-Medium.ttf"), 18)
    d.text((box[0] + 14, box[1] + (box[3] - box[1]) // 2 - 12), "apikey_••••••••••••••••••••",
           font=mono, fill=(0x55, 0x55, 0x55))


def highlight(img, box, step, label, arrow_from):
    """Amber box around the target, a numbered badge, and an arrow with a label."""
    d = ImageDraw.Draw(img)
    pad = 6
    x0, y0, x1, y1 = box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad
    for w in range(4):
        d.rounded_rectangle([x0 - w, y0 - w, x1 + w, y1 + w], radius=10, outline=AMBER)

    # arrow from the label toward the nearest edge midpoint of the box
    ax, ay = arrow_from
    tx = min(max(ax, x0), x1)
    ty = min(max(ay, y0), y1)
    d.line([(ax, ay), (tx, ty)], fill=AMBER, width=5)
    import math
    ang = math.atan2(ty - ay, tx - ax)
    head = 18
    for sign in (-1, 1):
        hx = tx - head * math.cos(ang + sign * 0.45)
        hy = ty - head * math.sin(ang + sign * 0.45)
        d.line([(tx, ty), (hx, hy)], fill=AMBER, width=5)

    # label pill with the step number
    f = font(26)
    text_w = d.textlength(label, font=f)
    r = 20
    pill_w = int(text_w + 2 * r + 34)
    px, py = ax - pill_w // 2, ay - r - 2
    d.rounded_rectangle([px, py, px + pill_w, py + 2 * r + 4], radius=r + 2, fill=INK)
    cx, cy = px + r + 4, py + r + 2
    d.ellipse([cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3], fill=AMBER)
    nf = font(24, "Bold")
    n = str(step)
    d.text((cx - d.textlength(n, font=nf) / 2, cy - 16), n, font=nf, fill=INK)
    d.text((cx + r + 8, cy - 18), label, font=f, fill=WHITE)


STEPS = [
    # raw file, extra blurs, dialog kept sharp, key mask, target box, label, label position
    ("01-home.jpg",    [],     None,                  None,                 (8, 182, 256, 214),   "Open API Keys",            (132, 420)),
    ("02-keys.jpg",    [ROWS], None,                  None,                 (1361, 14, 1479, 47), "Click Create key",         (1180, 560)),
    ("03-name.jpg",    [ROWS], (492, 281, 1021, 527), None,                 (517, 410, 996, 502), "Name it, then Create key", (756, 640)),
    ("04-created.jpg", [ROWS], (492, 266, 1021, 542), (517, 354, 914, 434), (922, 378, 996, 410), "Copy it now: shown once",  (1180, 640)),
]


def main(raw_dir: Path) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for i, (name, blurs, dialog, key_box, target, label, label_at) in enumerate(STEPS, start=1):
        img = Image.open(raw_dir / name).convert("RGB")
        if img.size != (1512, 807):
            sys.exit(f"{name}: expected 1512x807, got {img.size}")
        sharp = img.crop(dialog) if dialog else None
        blur(img, ACCOUNT)
        for box in blurs:
            blur(img, box)
        if sharp:
            img.paste(sharp, dialog[:2])     # the dialog is the subject; keep it readable
        if key_box:
            mask_key(img, key_box)
        highlight(img, target, i, label, label_at)
        out = OUT / f"step-{i}.png"
        img.resize((1210, 646), Image.LANCZOS).save(out, optimize=True)
        print(f"wrote {out}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]))
