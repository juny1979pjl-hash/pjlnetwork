#!/usr/bin/env python3
"""Animate a briefing-style map: flight paths draw themselves over a terrain image,
missile markers ride the path heads, target reticles pulse, radar rings sweep, and an
optional countdown tag ticks. Output is an MP4 ready for build_video.py.

  make_map.py terrain.png map01.mp4 --aspect 16:9 --duration 6 \
      --path "0.08,0.92 0.30,0.70 0.45,0.55 0.62,0.30" --formation 6 \
      --target 0.64,0.28 --radar 0.40,0.40,0.18 --countdown 31:54

Coordinates are fractions of the frame (0,0 = top left, 1,1 = bottom right), so they
stay valid for any aspect. Look at the terrain image first and place points along
valleys/riverbeds so the path reads as terrain-following.

  --path       "x,y x,y ..." control points, repeatable for separate routes
  --formation  draw N parallel copies of each path (a missile stream)
  --target     x,y red pulsing reticle, repeatable
  --radar      x,y,r red dashed coverage ring with a rotating sweep (r = fraction of width), repeatable
  --countdown  MM:SS countdown tag in the top-left, e.g. time to impact
  --zoom       end zoom factor for the slow push-in (default 1.08)
"""
import argparse
import math
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZES = {"16:9": (1920, 1080), "9:16": (1080, 1920)}
YELLOW, RED, WHITE = (255, 214, 0), (230, 40, 40), (255, 255, 255)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def cover(img, w, h):
    s = max(w / img.width, h / img.height)
    img = img.resize((math.ceil(img.width * s), math.ceil(img.height * s)), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def catmull(points, n=240):
    """Smooth the control points into n samples."""
    if len(points) < 3:
        (x0, y0), (x1, y1) = points[0], points[-1]
        return [(x0 + (x1 - x0) * i / (n - 1), y0 + (y1 - y0) * i / (n - 1)) for i in range(n)]
    pts = [points[0]] + points + [points[-1]]
    out, segs = [], len(points) - 1
    per = max(n // segs, 2)
    for i in range(segs):
        p0, p1, p2, p3 = pts[i], pts[i + 1], pts[i + 2], pts[i + 3]
        for k in range(per):
            t = k / per
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(points[-1])
    return out


def offset(path, dist):
    """Parallel copy of a path, shifted dist pixels to its left."""
    out = []
    for i, (x, y) in enumerate(path):
        a, b = path[max(i - 1, 0)], path[min(i + 1, len(path) - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        out.append((x - dy / L * dist, y + dx / L * dist))
    return out


def dashed(d, pts, color, width, dash=18, gap=12):
    acc, on = 0.0, True
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        if on:
            d.line([(x0, y0), (x1, y1)], fill=color, width=width)
        acc += seg
        if acc >= (dash if on else gap):
            acc, on = 0.0, not on


def font(size):
    for fam in ("Inter:style=Bold", "DejaVu Sans:style=Bold"):
        r = subprocess.run(["fc-match", "-f", "%{file}", fam], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return ImageFont.truetype(r.stdout.strip(), size)
    return ImageFont.load_default(size)


def parse_xy(s):
    return [tuple(float(v) for v in p.split(",")) for p in s.split()]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("background")
    p.add_argument("out")
    p.add_argument("--aspect", choices=SIZES, default="16:9")
    p.add_argument("--duration", type=float, default=6.0)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--path", action="append", default=[])
    p.add_argument("--formation", type=int, default=1)
    p.add_argument("--target", action="append", default=[])
    p.add_argument("--radar", action="append", default=[])
    p.add_argument("--countdown", default="")
    p.add_argument("--zoom", type=float, default=1.08)
    a = p.parse_args()
    if not a.path and not a.target and not a.radar:
        sys.exit("give at least one --path, --target or --radar")

    w, h = SIZES[a.aspect]
    s = min(w, h) / 1080
    bg = cover(Image.open(a.background).convert("RGB"), w, h)
    # darken a touch and cool it down so the overlays pop
    bg = Image.blend(bg, Image.new("RGB", (w, h), (10, 20, 30)), 0.18)

    routes = []
    for spec in a.path:
        base = catmull([(x * w, y * h) for x, y in parse_xy(spec)])
        n = max(a.formation, 1)
        spread = 22 * s
        for k in range(n):
            routes.append((offset(base, (k - (n - 1) / 2) * spread), k * 0.06))
    targets = [(x * w, y * h) for x, y in (map(float, t.split(",")) for t in a.target)]
    radars = [(x * w, y * h, r * w) for x, y, r in (map(float, t.split(",")) for t in a.radar)]
    if a.countdown:
        mm, ss = (int(v) for v in a.countdown.split(":"))
        start_secs = mm * 60 + ss
    tag_font = font(int(40 * s))

    frames = int(round(a.duration * a.fps))
    draw_time = a.duration * 0.75  # paths finish drawing at 75%, then hold
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{w}x{h}", "-r", str(a.fps), "-i", "-", "-c:v", "libx264",
                            "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", a.out],
                           stdin=subprocess.PIPE)
    for i in range(frames):
        t = i / a.fps
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        # radar rings + sweep
        for x, y, r in radars:
            ring = [(x + r * math.cos(k / 90 * math.pi), y + r * math.sin(k / 90 * math.pi)) for k in range(181)]
            dashed(d, ring, RED + (230,), max(2, int(4 * s)), dash=int(26 * s), gap=int(16 * s))
            ang = t * 120
            d.pieslice([x - r, y - r, x + r, y + r], ang - 35, ang, fill=RED + (55,))
            d.ellipse([x - 8 * s, y - 8 * s, x + 8 * s, y + 8 * s], fill=RED + (255,))
        # paths
        heads = []
        for pts, delay in routes:
            pr = ease((t - delay) / draw_time)
            n = int(len(pts) * pr)
            if n >= 2:
                dashed(d, pts[:n], YELLOW + (255,), max(2, int(4 * s)), dash=int(16 * s), gap=int(10 * s))
                heads.append(pts[n - 1])
        # targets
        for x, y in targets:
            pulse = 1 + 0.18 * math.sin(t * 6)
            for rr, wd in ((46, 5), (30, 4)):
                R = rr * s * pulse
                d.ellipse([x - R, y - R, x + R, y + R], outline=RED + (255,), width=max(2, int(wd * s)))
            L = 62 * s * pulse
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                d.line([(x + dx * L * 0.55, y + dy * L * 0.55), (x + dx * L, y + dy * L)],
                       fill=RED + (255,), width=max(2, int(4 * s)))
        # glow: blur a copy of the overlay at half size, add it under the sharp one
        small = layer.resize((w // 2, h // 2))
        glow = small.filter(ImageFilter.GaussianBlur(6 * s)).resize((w, h))
        frame = bg.copy()
        frame.paste(glow, (0, 0), glow)
        frame.paste(layer, (0, 0), layer)
        fd = ImageDraw.Draw(frame)
        for x, y in heads:  # missile markers
            R = 7 * s
            fd.ellipse([x - R * 2.2, y - R * 2.2, x + R * 2.2, y + R * 2.2], outline=YELLOW, width=max(1, int(2 * s)))
            fd.ellipse([x - R, y - R, x + R, y + R], fill=WHITE)
        if a.countdown:
            left = max(start_secs - int(t), 0)
            txt = f"{left // 60}m {left % 60:02d}s"
            pad = int(14 * s)
            x0, y0 = int(40 * s), int(h * 0.14) if h > w else int(40 * s)
            tw = fd.textlength(txt, font=tag_font)
            fd.rectangle([x0, y0, x0 + tw + 2 * pad, y0 + tag_font.size + 2 * pad], fill=YELLOW)
            fd.text((x0 + pad, y0 + pad * 0.7), txt, font=tag_font, fill=(0, 0, 0))
        # slow push-in on the whole composite
        z = 1 + (a.zoom - 1) * (i / max(frames - 1, 1))
        if z > 1.0001:
            cw, ch = w / z, h / z
            frame = frame.crop(((w - cw) / 2, (h - ch) / 2, (w + cw) / 2, (h + ch) / 2)).resize((w, h), Image.BILINEAR)
        enc.stdin.write(frame.tobytes())
    enc.stdin.close()
    if enc.wait():
        sys.exit("ffmpeg failed")
    print(a.out)


if __name__ == "__main__":
    main()
