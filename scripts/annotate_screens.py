#!/usr/bin/env python3
"""Annotate the README walkthrough screenshots.

The raw captures hold account details, and the API key ones a live key, so they
never enter the repo. Capture them yourself, then run:

    python3 scripts/annotate_screens.py api-key /path/to/raw-dir
    python3 scripts/annotate_screens.py plugin-marketplace /path/to/raw-dir

api-key: 1512x807 captures of console.typesafe.ai, named 01-home.jpg,
02-keys.jpg, 03-name.jpg, 04-created.jpg.
plugin-marketplace: 1510x812 captures of claude.ai/customize/plugins with a dark
theme, named 01-add-menu.jpg, 02-chooser.jpg, 03-repo.jpg, 04-listed.jpg,
05-installed.jpg.
Each flow writes .github/assets/<flow>/step-1.png onward.

Every image gets the same treatment: blur the account details (and, for API
keys, every existing key row and the new key's value), then draw an amber
highlight box, a numbered badge, and an arrow with a label on the one control
the step is about. Coordinates are in the capture frame.
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "assets" / "fonts"
ASSETS = ROOT / ".github" / "assets"

AMBER = (0xD9, 0x8B, 0x0B)
INK = (0x1B, 0x19, 0x16)
WHITE = (0xFF, 0xFF, 0xFF)

ACCOUNT = (0, 740, 265, 807)            # avatar, name, org
ROWS = (298, 162, 1480, 436)            # every key row: names, prefixes, creator
SIDEBAR = (0, 300, 288, 812)            # claude.ai: projects, pins, chat titles, account


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


# flow: (capture size, output size, steps). Each step is
# raw file, blurs, dialog kept sharp, key mask, target box, label, label position.
FLOWS = {
    "api-key": ((1512, 807), (1210, 646), [
        ("01-home.jpg",    [ACCOUNT],       None,                  None,                 (8, 182, 256, 214),   "Open API Keys",            (132, 420)),
        ("02-keys.jpg",    [ACCOUNT, ROWS], None,                  None,                 (1361, 14, 1479, 47), "Click Create key",         (1180, 560)),
        ("03-name.jpg",    [ACCOUNT, ROWS], (492, 281, 1021, 527), None,                 (517, 410, 996, 502), "Name it, then Create key", (756, 640)),
        ("04-created.jpg", [ACCOUNT, ROWS], (492, 266, 1021, 542), (517, 354, 914, 434), (922, 378, 996, 410), "Copy it now: shown once",  (1180, 640)),
    ]),
    "plugin-marketplace": ((1510, 812), (1208, 650), [
        ("01-add-menu.jpg",  [SIDEBAR], None, None, (1206, 159, 1388, 193),  "Add, then Add marketplace", (1100, 330)),
        ("02-chooser.jpg",   [SIDEBAR], None, None, (410, 410, 1102, 479),   "Add from a repository",     (755, 660)),
        ("03-repo.jpg",      [SIDEBAR], None, None, (409, 405, 1102, 586),   "Enter the repo, then Sync", (755, 690)),
        ("04-listed.jpg",    [SIDEBAR], None, None, (1338, 190, 1389, 224),  "Add the plugin",            (1180, 258)),
        ("05-installed.jpg", [SIDEBAR], None, None, (1132, 735, 1484, 795),  "Installed and ready",       (1000, 600)),
    ]),
}


def main(flow: str, raw_dir: Path) -> None:
    size, out_size, steps = FLOWS[flow]
    out_dir = ASSETS / flow
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, (name, blurs, dialog, key_box, target, label, label_at) in enumerate(steps, start=1):
        img = Image.open(raw_dir / name).convert("RGB")
        if img.size != size:
            sys.exit(f"{name}: expected {size[0]}x{size[1]}, got {img.size}")
        sharp = img.crop(dialog) if dialog else None
        for box in blurs:
            blur(img, box)
        if sharp:
            img.paste(sharp, dialog[:2])     # the dialog is the subject; keep it readable
        if key_box:
            mask_key(img, key_box)
        highlight(img, target, i, label, label_at)
        out = out_dir / f"step-{i}.png"
        img.resize(out_size, Image.LANCZOS).save(out, optimize=True)
        print(f"wrote {out}")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in FLOWS:
        sys.exit(__doc__)
    main(sys.argv[1], Path(sys.argv[2]))
