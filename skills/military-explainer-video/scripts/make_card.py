#!/usr/bin/env python3
"""Render text cards (spec / stat / clock / title) as PNGs with Pillow.

Text is drawn locally so names and numbers are always exact — image models garble text.

Examples:
  make_card.py spec  out.png --aspect 16:9 --name "BGM-109 Tomahawk" --variant "Block V" \
      --stat "Weight=3,500 lb" --stat "Length=20 ft" --stat "Speed=550 mph" \
      --stat "Warhead=1,000 lb" --stat "Range=~1,000 mi" [--image tomahawk.png]
  make_card.py stat  out.png --aspect 9:16 --big "93 → 20 mi" --label "Radar reach vs. a 50-ft target"
  make_card.py clock out.png --aspect 16:9 --big "05:38" --label "LOCAL TIME"
  make_card.py title out.png --aspect 9:16 --big "How 12 Tomahawks Beat the Radar" --tag SCENARIO
"""
import argparse
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

SIZES = {"16:9": (1920, 1080), "9:16": (1080, 1920)}
BG_TOP, BG_BOTTOM = (14, 22, 30), (4, 8, 12)
AMBER, WHITE, MUTED, RED = (255, 196, 0), (240, 244, 248), (150, 165, 180), (220, 50, 47)


def font(weight, size):
    """Find a sans font via fontconfig (Inter preferred, DejaVu fallback)."""
    for family in (f"Inter:style={weight}", f"DejaVu Sans:style={weight}", "DejaVu Sans"):
        try:
            path = subprocess.run(["fc-match", "-f", "%{file}", family],
                                  capture_output=True, text=True, check=True).stdout.strip()
            if path:
                return ImageFont.truetype(path, size)
        except (OSError, subprocess.CalledProcessError):
            continue
    return ImageFont.load_default(size)


def background(w, h):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(BG_TOP[i] * (1 - t) + BG_BOTTOM[i] * t) for i in range(3)))
    # faint grid, like a briefing screen
    step = w // 24
    for x in range(0, w, step):
        d.line([(x, 0), (x, h)], fill=(22, 34, 44))
    for y in range(0, h, step):
        d.line([(0, y), (w, y)], fill=(22, 34, 44))
    return img


def wrap(d, text, f, max_w):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if d.textlength(trial, font=f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def tag(d, x, y, text, f, color):
    pad = int(f.size * 0.35)
    tw = d.textlength(text, font=f)
    d.rectangle([x, y, x + tw + 2 * pad, y + f.size + 2 * pad], fill=color)
    d.text((x + pad, y + pad * 0.6), text, font=f, fill=(0, 0, 0))
    return y + f.size + 2 * pad


def spec(a, w, h):
    img = background(w, h)
    d = ImageDraw.Draw(img)
    s = min(w, h) / 1080
    m = int(90 * s)
    vertical = h > w
    top = int(h * 0.14) if vertical else m  # keep clear of phone UI at the top
    y = tag(d, m, top, a.name, font("Bold", int(64 * s)), AMBER)
    if a.variant:
        y = tag(d, m + int(20 * s), y, a.variant, font("Bold", int(34 * s)), WHITE)
    y += int(40 * s)
    if a.image:
        pic = Image.open(a.image).convert("RGBA")
        box_w = w - 2 * m if vertical else int(w * 0.5)
        box_h = int(h * 0.3) if vertical else h - y - m
        pic.thumbnail((box_w, box_h))
        px = (w - pic.width) // 2 if vertical else w - m - pic.width
        py = y if vertical else y + (box_h - pic.height) // 2
        img.paste(pic, (px, py), pic)
        if vertical:
            y += pic.height + int(40 * s)
    lab_f, val_f = font("Medium", int(40 * s)), font("Bold", int(58 * s))
    col_w = (w - 2 * m) if (vertical or not a.image) else int(w * 0.42)
    for item in a.stat:
        label, _, value = item.partition("=")
        d.text((m, y), label.upper(), font=lab_f, fill=MUTED)
        vw = d.textlength(value, font=val_f)
        d.text((m + col_w - vw, y - int(10 * s)), value, font=val_f, fill=WHITE)
        y += int(70 * s)
        d.line([(m, y), (m + col_w, y)], fill=(60, 75, 90), width=max(1, int(2 * s)))
        y += int(26 * s)
    return img


def big_text(a, w, h, accent):
    img = background(w, h)
    d = ImageDraw.Draw(img)
    s = min(w, h) / 1080
    m = int(90 * s)
    size = int((150 if a.mode != "title" else 110) * s)
    f = font("Bold", size)
    lines = wrap(d, a.big, f, w - 2 * m)
    total = len(lines) * size * 1.15 + (size * 0.8 if a.label else 0)
    y = (h - total) / 2
    if a.tag:
        tf = font("Bold", int(40 * s))
        tag(d, (w - d.textlength(a.tag, font=tf)) / 2 - tf.size * 0.35, y - tf.size * 2.4, a.tag, tf, RED)
    for line in lines:
        d.text(((w - d.textlength(line, font=f)) / 2, y), line, font=f, fill=accent)
        y += size * 1.15
    if a.label:
        lf = font("Medium", int(48 * s))
        for line in wrap(d, a.label.upper(), lf, w - 2 * m):
            d.text(((w - d.textlength(line, font=lf)) / 2, y + size * 0.2), line, font=lf, fill=MUTED)
            y += lf.size * 1.3
    return img


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode", choices=["spec", "stat", "clock", "title"])
    p.add_argument("out")
    p.add_argument("--aspect", choices=SIZES, default="16:9")
    p.add_argument("--name", default="")
    p.add_argument("--variant", default="")
    p.add_argument("--stat", action="append", default=[], help="LABEL=VALUE, repeatable")
    p.add_argument("--image", help="optional weapon render for spec cards")
    p.add_argument("--big", default="")
    p.add_argument("--label", default="")
    p.add_argument("--tag", default="", help="e.g. SCENARIO")
    a = p.parse_args()
    w, h = SIZES[a.aspect]
    if a.mode == "spec":
        if not a.name or not a.stat:
            sys.exit("spec cards need --name and at least one --stat")
        img = spec(a, w, h)
    else:
        if not a.big:
            sys.exit(f"{a.mode} cards need --big")
        img = big_text(a, w, h, AMBER if a.mode != "title" else WHITE)
    img.save(a.out)
    print(a.out)


if __name__ == "__main__":
    main()
