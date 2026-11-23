import sys, subprocess, math
import numpy as np
import cv2
from PIL import Image, ImageDraw
from gfx import *
import scenes as SC

FPS = 30
XF = 0.5  # crossfade seconds


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def blit(frame, arr, x, y, alpha=1.0):
    """Alpha-composite RGBA numpy array onto RGB float frame."""
    h, w = arr.shape[:2]
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0 or alpha <= 0:
        return
    sub = arr[y0 - y:y1 - y, x0 - x:x1 - x]
    a = sub[..., 3:4].astype(np.float32) * (alpha / 255.0)
    frame[y0:y1, x0:x1] = frame[y0:y1, x0:x1] * (1 - a) + sub[..., :3] * a


def render_counter(c, t):
    p = ease((t - c.t_in) / c.t_dur)
    v = c.v0 + (c.v1 - c.v0) * p
    txt = c.fmt.format(v).replace(',', '.') + c.suffix
    if '.' in c.fmt and 'f}' in c.fmt and ':.1f' in c.fmt:
        txt = c.fmt.format(v).replace('.', ',') + c.suffix
    if txt not in c.cache:
        c.cache[txt] = np.array(text_block(txt, c.size, 'Black', c.color, align='center'))
    arr = c.cache[txt]
    h, w = arr.shape[:2]
    x = int(c.x - w / 2) if c.align == 'center' else int(c.x)
    return arr, x, int(c.y - h / 2)


def scene_frame(sc, t):
    if sc.bg_arr is None:
        sc.bg_arr = np.array(sc.bg.convert('RGB'))
    p = (t - sc.start) / max(sc.end - sc.start, 0.01)
    p = min(max(p, 0), 1)
    z = sc.kb[0] + (sc.kb[1] - sc.kb[0]) * (p * p * (3 - 2 * p))
    cw = BW / z
    ch = cw * H / W
    k = W / cw
    mx, my = (BW - cw) / 2, (BH - ch) / 2
    x0 = mx + sc.pan[0] * (p - 0.5) * 2 * (mx / max(mx, 1e-6)) * 0 + mx * 0 + sc.pan[0] * (p - 0.5)
    x0 = (BW - cw) / 2 + sc.pan[0] * (p - 0.5) * 2
    y0 = (BH - ch) / 2 + sc.pan[1] * (p - 0.5) * 2
    x0 = min(max(x0, 0), BW - cw)
    y0 = min(max(y0, 0), BH - ch)
    M = np.float32([[k, 0, -x0 * k], [0, k, -y0 * k]])
    fr = cv2.warpAffine(sc.bg_arr, M, (W, H), flags=cv2.INTER_LINEAR).astype(np.float32)
    for it in sc.items:
        if isinstance(it, SC.Counter):
            if t < it.t_in:
                continue
            arr, x, y = render_counter(it, t)
            a = ease((t - it.t_in) / 0.3)
            blit(fr, arr, x, y, a)
            continue
        if t < it.t_in or (it.t_out and t > it.t_out):
            continue
        q = ease((t - it.t_in) / it.dur)
        x, y, arr = it.x, it.y, it.arr
        if it.anim == 'up':
            y = int(y + (1 - q) * 40)
        elif it.anim == 'left':
            x = int(x - (1 - q) * 60)
        elif it.anim == 'grow':
            w = max(1, int(arr.shape[1] * q))
            blit(fr, arr[:, :w], x, y, 1.0)
            continue
        blit(fr, arr, x, y, q)
    return fr


# ------------------------------------------------------------ global overlays
def make_bug():
    img = Image.new('RGBA', (560, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 150, 64], fill=RED)
    d.text((18, 14), 'ESPECIAL', font=font(28, 'Black'), fill=WHITE)
    d.rectangle([150, 0, 560, 64], fill=(7, 18, 38, 215))
    d.text((170, 15), 'BUKELE EN HAITÍ', font=font(28, 'Bold'), fill=WHITE)
    return np.array(img)


def make_ticker():
    f = font(30, 'Semi')
    tmp = ImageDraw.Draw(Image.new('L', (1, 1)))
    tw = int(tmp.textlength(SC.TICKER, font=f))
    strip = Image.new('RGBA', (tw * 2, 54), (0, 0, 0, 0))
    d = ImageDraw.Draw(strip)
    d.text((0, 9), SC.TICKER, font=f, fill=WHITE)
    d.text((tw, 9), SC.TICKER, font=f, fill=WHITE)
    base = Image.new('RGBA', (W, 54), (7, 18, 38, 235))
    lab = Image.new('RGBA', (230, 54), RED + (255,))
    ImageDraw.Draw(lab).text((20, 10), 'ÚLTIMA HORA', font=font(28, 'Black'), fill=WHITE)
    return np.array(base), np.array(strip), tw, np.array(lab)


def make_lower(title, subtitle):
    ft, fs = font(44, 'Black'), font(30, 'Semi')
    tmp = ImageDraw.Draw(Image.new('L', (1, 1)))
    w = int(max(tmp.textlength(title, font=ft), tmp.textlength(subtitle, font=fs))) + 80
    img = Image.new('RGBA', (w + 16, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 14, 128], fill=RED)
    d.rectangle([16, 0, w + 16, 74], fill=(255, 255, 255, 245))
    d.text((40, 12), title, font=ft, fill=NAVY)
    d.rectangle([16, 74, w + 16, 128], fill=(139, 18, 30, 240))
    d.text((40, 84), subtitle, font=fs, fill=WHITE)
    return np.array(img)


BUG = make_bug()
TK_BASE, TK_STRIP, TK_W, TK_LAB = make_ticker()
LOWERS = []
for i, (t, a, b) in enumerate(SC.LOWER_THIRDS):
    nxt = SC.LOWER_THIRDS[i + 1][0] if i + 1 < len(SC.LOWER_THIRDS) else 9999
    LOWERS.append((t, min(t + 7.0, nxt - 0.3), make_lower(a, b)))


def overlays(fr, t):
    on = 12.0 < t < SC.VO4_END
    if on:
        blit(fr, BUG, 60, 48, ease((t - 12.0) / 0.5))
        # ticker
        a = ease((t - 12.0) / 0.5)
        blit(fr, TK_BASE, 0, H - 54, a)
        off = int((t * 110) % TK_W)
        blit(fr, TK_STRIP[:, off:off + W], 240, H - 54, a)
        blit(fr, TK_LAB, 0, H - 54, a)
    for t0, t1, arr in LOWERS:
        if t0 <= t <= t1 + 0.4:
            q = ease((t - t0) / 0.5) if t < t1 else 1 - ease((t - t1) / 0.4)
            x = int(90 - (1 - q) * 120)
            blit(fr, arr, x, 760, q)


def main(t_start, t_end, out):
    S = SC.build()
    starts = [s.start for s in S]
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                           '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', out],
                          stdin=subprocess.PIPE)
    n0, n1 = int(round(t_start * FPS)), int(round(t_end * FPS))
    for n in range(n0, n1):
        t = n / FPS
        i = max(j for j, s in enumerate(starts) if s <= t + 1e-6)
        fr = scene_frame(S[i], t)
        if i > 0 and t < S[i].start + XF:
            a = ease((t - S[i].start) / XF)
            prev = scene_frame(S[i - 1], t)
            fr = prev * (1 - a) + fr * a
        if t < 0.6:
            fr *= t / 0.6
        if t > SC.TOTAL - 1.0:
            fr *= max(0, (SC.TOTAL - t) / 1.0)
        overlays(fr, t)
        ff.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
        if n % 900 == 0:
            print(out, '%.0f s' % t, flush=True)
    ff.stdin.close()
    ff.wait()


if __name__ == '__main__':
    if sys.argv[1] == 'still':
        S = SC.build()
        starts = [s.start for s in S]
        for t in map(float, sys.argv[2:]):
            i = max(j for j, s in enumerate(starts) if s <= t)
            fr = scene_frame(S[i], t)
            overlays(fr, t)
            Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8)).resize((960, 540)).save('still_%06.1f.jpg' % t)
    else:
        main(float(sys.argv[1]), float(sys.argv[2]), sys.argv[3])
