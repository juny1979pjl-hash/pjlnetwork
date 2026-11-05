#!/usr/bin/env python3
"""Render text cards (spec / stat / clock / title) as animated MP4s or still PNGs.

Text is drawn locally so names and numbers are always exact — image models garble text.
Give an .mp4 output for an animated card (elements slide in, numbers count up, tags
flash); give a .png for a still.

Examples:
  make_card.py spec  spec.mp4 --aspect 16:9 --name "BGM-109 Tomahawk" --variant "Block V" \
      --stat "Weight=3,500 lb" --stat "Length=20 ft" --stat "Speed=550 mph" \
      --stat "Warhead=1,000 lb" --stat "Range=~1,000 mi" [--image tomahawk.png] [--duration 5]
  make_card.py stat  stat.mp4  --aspect 9:16 --big "93 → 20 mi" --label "Radar reach vs. a 50-ft target"
  make_card.py clock clock.mp4 --aspect 16:9 --big "05:38" --label "LOCAL TIME"
  make_card.py title title.mp4 --aspect 9:16 --big "How 12 Tomahawks Beat the Radar" --tag SCENARIO
"""
import argparse
import re
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

SIZES = {"16:9": (1920, 1080), "9:16": (1080, 1920)}
BG_TOP, BG_BOTTOM = (14, 22, 30), (4, 8, 12)
AMBER, WHITE, MUTED, RED = (255, 196, 0), (240, 244, 248), (150, 165, 180), (220, 50, 47)
_fonts = {}


def font(weight, size):
    """Find a sans font via fontconfig (Inter preferred, DejaVu fallback)."""
    key = (weight, size)
    if key not in _fonts:
        _fonts[key] = None
        for family in (f"Inter:style={weight}", f"DejaVu Sans:style={weight}", "DejaVu Sans"):
            try:
                path = subprocess.run(["fc-match", "-f", "%{file}", family],
                                      capture_output=True, text=True, check=True).stdout.strip()
                if path:
                    _fonts[key] = ImageFont.truetype(path, size)
                    break
            except (OSError, subprocess.CalledProcessError):
                continue
        if _fonts[key] is None:
            _fonts[key] = ImageFont.load_default(size)
    return _fonts[key]


# ---------- animation helpers
def ease(x):
    """Ease-out cubic on 0..1 (clamped)."""
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def prog(t, start, dur):
    return ease((t - start) / dur) if dur > 0 else float(t >= start)


NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def count_up(text, p):
    """Replace each number in text with its value * p, keeping commas/decimals."""
    if p >= 1:
        return text

    def sub(m):
        s = m.group(0)
        dec = len(s.split(".")[1]) if "." in s else 0
        v = float(s.replace(",", "")) * p
        out = f"{v:,.{dec}f}" if "," in s else f"{v:.{dec}f}"
        # keep leading zeros on things like 05
        return out.zfill(len(s)) if s.startswith("0") and "," not in s else out

    return NUM.sub(sub, text)


# ---------- drawing
def background(w, h):
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(BG_TOP[i] * (1 - t) + BG_BOTTOM[i] * t) for i in range(3)))
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


def tag(d, x, y, text, f, color, reveal=1.0):
    """Label on a colored bar; reveal 0..1 wipes the bar in from the left."""
    pad = int(f.size * 0.35)
    tw = d.textlength(text, font=f)
    full = tw + 2 * pad
    bw = full * reveal
    if bw > 1:
        d.rectangle([x, y, x + bw, y + f.size + 2 * pad], fill=color)
        if reveal > 0.6:
            d.text((x + pad, y + pad * 0.6), text, font=f, fill=(0, 0, 0))
    return y + f.size + 2 * pad


def spec(a, w, h, bg, t):
    img = bg.copy()
    d = ImageDraw.Draw(img, "RGBA")
    s = min(w, h) / 1080
    m = int(90 * s)
    vertical = h > w
    y = int(h * 0.14) if vertical else m  # keep clear of phone UI at the top
    y = tag(d, m, y, a.name, font("Bold", int(64 * s)), AMBER, prog(t, 0.0, 0.35))
    if a.variant:
        y = tag(d, m + int(20 * s), y, a.variant, font("Bold", int(34 * s)), WHITE, prog(t, 0.2, 0.3))
    y += int(40 * s)
    if a.image:
        pic = Image.open(a.image).convert("RGBA")
        box_w = w - 2 * m if vertical else int(w * 0.5)
        box_h = int(h * 0.3) if vertical else h - y - m
        pic.thumbnail((box_w, box_h))
        p = prog(t, 0.3, 0.7)
        if p > 0:
            px = (w - pic.width) // 2 if vertical else w - m - pic.width
            py = y if vertical else y + (box_h - pic.height) // 2
            px += int((1 - p) * w * 0.25)  # slide in from the right
            faded = pic.copy()
            faded.putalpha(faded.getchannel("A").point(lambda v: int(v * p)))
            img.paste(faded, (px, py), faded)
        if vertical:
            y += pic.height + int(40 * s)
    lab_f, val_f = font("Medium", int(40 * s)), font("Bold", int(58 * s))
    col_w = (w - 2 * m) if (vertical or not a.image) else int(w * 0.42)
    for i, item in enumerate(a.stat):
        label, _, value = item.partition("=")
        start = 0.5 + 0.18 * i
        p = prog(t, start, 0.3)
        if p > 0:
            dx = int((1 - p) * -60 * s)
            alpha = int(255 * p)
            d.text((m + dx, y), label.upper(), font=lab_f, fill=MUTED + (alpha,))
            shown = count_up(value, prog(t, start, 0.9))
            vw = d.textlength(shown, font=val_f)
            d.text((m + col_w - vw, y - int(10 * s)), shown, font=val_f, fill=WHITE + (alpha,))
            ly = y + int(70 * s)
            d.line([(m, ly), (m + col_w * p, ly)], fill=(255, 196, 0, 160), width=max(1, int(3 * s)))
        y += int(96 * s)
    return img


def big_text(a, w, h, bg, t):
    img = bg.copy()
    d = ImageDraw.Draw(img, "RGBA")
    s = min(w, h) / 1080
    m = int(90 * s)
    accent = WHITE if a.mode == "title" else AMBER
    base = int((150 if a.mode != "title" else 110) * s)
    pop = 1 + 0.25 * (1 - prog(t, 0.0, 0.35))  # punch in from 125% to 100%
    size = int(base * pop)
    f = font("Bold", size)
    text = a.big
    if a.mode == "stat":
        text = count_up(text, prog(t, 0.1, 1.0))
    elif a.mode == "clock":
        # type the digits in, then blink the colon
        n = int(len(text) * prog(t, 0.0, 0.5) + 0.999)
        text = text[:n]
        if t > 0.6 and int(t * 2) % 2:
            text = text.replace(":", " ")
    lines = wrap(d, a.big, font("Bold", base), w - 2 * m) if a.mode == "title" else [text]
    if a.mode == "title":
        # reveal words one by one
        words_shown = int(len(a.big.split()) * prog(t, 0.0, 0.9) + 0.999)
        out, k = [], 0
        for line in lines:
            ws = line.split()
            out.append(" ".join(ws[: max(0, words_shown - k)]))
            k += len(ws)
        lines = out
    total = len(lines) * size * 1.15 + (size * 0.8 if a.label else 0)
    y = (h - total) / 2
    if a.tag:
        tf = font("Bold", int(40 * s))
        on = t < 0.15 or t > 0.8 or int(t * 8) % 2 == 0  # flash a few times
        if on:
            tag(d, (w - d.textlength(a.tag, font=tf)) / 2 - tf.size * 0.35, y - tf.size * 2.4, a.tag, tf, RED)
    for line in lines:
        d.text(((w - d.textlength(line, font=f)) / 2, y), line, font=f, fill=accent)
        y += size * 1.15
    if a.label:
        p = prog(t, 0.4, 0.4)
        lf = font("Medium", int(48 * s))
        for line in wrap(d, a.label.upper(), lf, w - 2 * m):
            d.text(((w - d.textlength(line, font=lf)) / 2, y + size * 0.2 + (1 - p) * 30 * s),
                   line, font=lf, fill=MUTED + (int(255 * p),))
            y += lf.size * 1.3
    return img


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode", choices=["spec", "stat", "clock", "title"])
    p.add_argument("out", help=".mp4 for animated, .png for still")
    p.add_argument("--aspect", choices=SIZES, default="16:9")
    p.add_argument("--duration", type=float, default=4.0, help="seconds (animated only)")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--name", default="")
    p.add_argument("--variant", default="")
    p.add_argument("--stat", action="append", default=[], help="LABEL=VALUE, repeatable")
    p.add_argument("--image", help="optional weapon render for spec cards")
    p.add_argument("--big", default="")
    p.add_argument("--label", default="")
    p.add_argument("--tag", default="", help="e.g. SCENARIO")
    a = p.parse_args()
    if a.mode == "spec" and (not a.name or not a.stat):
        sys.exit("spec cards need --name and at least one --stat")
    if a.mode != "spec" and not a.big:
        sys.exit(f"{a.mode} cards need --big")
    w, h = SIZES[a.aspect]
    bg = background(w, h)
    draw = spec if a.mode == "spec" else big_text

    if not a.out.lower().endswith((".mp4", ".mov")):
        draw(a, w, h, bg, 99.0).save(a.out)  # final state
        print(a.out)
        return

    frames = int(round(a.duration * a.fps))
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{w}x{h}", "-r", str(a.fps), "-i", "-", "-c:v", "libx264",
                            "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", a.out],
                           stdin=subprocess.PIPE)
    for i in range(frames):
        enc.stdin.write(draw(a, w, h, bg, i / a.fps).tobytes())
    enc.stdin.close()
    if enc.wait():
        sys.exit("ffmpeg failed")
    print(a.out)


if __name__ == "__main__":
    main()
