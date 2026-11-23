import io, math, functools
import numpy as np
import cairosvg
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1920, 1080
BW, BH = 2112, 1188  # oversized background for Ken Burns

NAVY = (7, 18, 38)
NAVY2 = (16, 40, 74)
RED = (200, 16, 46)
DRED = (139, 18, 30)
GOLD = (242, 182, 50)
WHITE = (255, 255, 255)
GREY = (170, 182, 200)
LAND = (28, 52, 86)
LAND_STROKE = (74, 104, 142)

FONTDIR = '/usr/share/fonts/opentype/inter/'
MAP_SVG = open('../mapsrc/pygal_maps_world-1.0.2/pygal_maps_world/worldmap.svg').read()


@functools.lru_cache(None)
def font(size, weight='Bold'):
    name = {'Black': 'InterDisplay-Black.otf', 'Bold': 'InterDisplay-Bold.otf',
            'Extra': 'InterDisplay-ExtraBold.otf', 'Semi': 'Inter-SemiBold.otf',
            'Reg': 'Inter-Regular.otf', 'Med': 'Inter-Medium.otf',
            'Italic': 'Inter-SemiBoldItalic.otf'}[weight]
    return ImageFont.truetype(FONTDIR + name, size)


def hexc(c):
    return '#%02x%02x%02x' % c


# ---------------------------------------------------------------- backgrounds
@functools.lru_cache(None)
def base_bg(tint=0):
    """Navy gradient with faint grid and vignette (BW x BH)."""
    y = np.linspace(0, 1, BH)[:, None]
    x = np.linspace(0, 1, BW)[None, :]
    top = np.array(NAVY2, float)
    bot = np.array(NAVY, float)
    g = top * (1 - y[..., None]) + bot * y[..., None]
    g = np.broadcast_to(g, (BH, BW, 3)).copy()
    if tint:
        g[..., 0] += tint * (1 - x) * 18
    # vignette
    d = np.sqrt(((x - .5) * 1.6) ** 2 + ((y - .5) * 1.9) ** 2)
    g *= np.clip(1.15 - d * 0.55, 0.55, 1)[..., None]
    img = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img, 'RGBA')
    for gx in range(0, BW, 96):
        d.line([(gx, 0), (gx, BH)], fill=(255, 255, 255, 9))
    for gy in range(0, BH, 96):
        d.line([(0, gy), (BW, gy)], fill=(255, 255, 255, 9))
    return img


def map_image(cx, cy, span, highlight=None, dim=False, out=(BW, BH)):
    """Render a region of the world map. Map units come from the SVG viewBox."""
    highlight = highlight or {}
    ow, oh = out
    sx = span
    sy = span * oh / ow
    vb = (cx - sx / 2, cy - sy / 2, sx, sy)
    land = LAND if not dim else (20, 38, 64)
    css = ('<style>path{fill:%s;stroke:%s;stroke-width:%.3f;stroke-linejoin:round}' %
           (hexc(land), hexc(LAND_STROKE), max(0.05, span / 900)))
    for cc, col in highlight.items():
        css += '.%s path{fill:%s;stroke:#ffffff;stroke-width:%.3f}' % (cc, hexc(col), max(0.06, span / 600))
    css += '</style>'
    s = MAP_SVG.replace('viewBox="0 0 2475 1388"', 'viewBox="%f %f %f %f"' % vb, 1)
    s = s.replace('<g id="countries">', css + '<g id="countries">', 1)
    png = cairosvg.svg2png(bytestring=s.encode(), output_width=ow, output_height=oh)
    fg = Image.open(io.BytesIO(png)).convert('RGBA')
    bg = base_bg().copy().resize((ow, oh)) if (ow, oh) != (BW, BH) else base_bg().copy()
    bg = bg.convert('RGBA')
    # soft glow under land
    glow = fg.split()[3].filter(ImageFilter.GaussianBlur(18))
    glowimg = Image.new('RGBA', (ow, oh), (60, 120, 200, 0))
    glowimg.putalpha(glow.point(lambda a: int(a * 0.35)))
    bg.alpha_composite(glowimg)
    bg.alpha_composite(fg)

    def to_px(mx, my):
        return ((mx - vb[0]) / sx * ow, (my - vb[1]) / sy * oh)
    return bg, to_px


def draw_marker(img, xy, label=None, color=RED, r=14, side='right', size=34):
    d = ImageDraw.Draw(img, 'RGBA')
    x, y = xy
    for rr, a in ((r * 3.2, 40), (r * 2.2, 70)):
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=color + (a,))
    d.ellipse([x - r, y - r, x + r, y + r], fill=color + (255,), outline=WHITE, width=4)
    if label:
        f = font(size, 'Bold')
        tw = d.textlength(label, font=f)
        if side == 'right':
            tx = x + r * 2.6
        elif side == 'left':
            tx = x - r * 2.6 - tw
        else:
            tx = x - tw / 2
        ty = y - size * 0.62 if side != 'below' else y + r * 2
        pad = 10
        d.rounded_rectangle([tx - pad, ty - 6, tx + tw + pad, ty + size + 8], 6, fill=(0, 0, 0, 150))
        d.text((tx, ty), label, font=f, fill=WHITE)


def draw_arrow(img, p1, p2, color=GOLD, width=10, bend=0.25):
    d = ImageDraw.Draw(img, 'RGBA')
    (x1, y1), (x2, y2) = p1, p2
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    nx, ny = -(y2 - y1), (x2 - x1)
    cx, cy = mx + nx * bend, my + ny * bend
    pts = []
    for i in range(61):
        t = i / 60
        pts.append(((1 - t) ** 2 * x1 + 2 * (1 - t) * t * cx + t * t * x2,
                    (1 - t) ** 2 * y1 + 2 * (1 - t) * t * cy + t * t * y2))
    for i in range(0, 58, 4):
        d.line(pts[i:i + 3], fill=color + (255,), width=width)
    ax, ay = pts[-1]
    bx, by = pts[-6]
    ang = math.atan2(ay - by, ax - bx)
    L = width * 3.2
    d.polygon([(ax, ay), (ax - L * math.cos(ang - .45), ay - L * math.sin(ang - .45)),
               (ax - L * math.cos(ang + .45), ay - L * math.sin(ang + .45))], fill=color + (255,))


def world_texture():
    """Faint world map for card backgrounds."""
    img, _ = map_image(1237, 640, 2300, dim=True)
    return Image.blend(base_bg().convert('RGBA'), img, 0.45)


# --------------------------------------------------------------------- text
def text_block(lines, size=60, weight='Bold', color=WHITE, align='left', spacing=1.18,
               maxw=None, shadow=True):
    """Render (possibly wrapped) text to a tight RGBA image."""
    f = font(size, weight)
    if isinstance(lines, str):
        lines = [lines]
    out = []
    tmp = ImageDraw.Draw(Image.new('L', (10, 10)))
    for ln in lines:
        if maxw is None:
            out.append(ln)
            continue
        words, cur = ln.split(' '), ''
        for w_ in words:
            test = (cur + ' ' + w_).strip()
            if tmp.textlength(test, font=f) <= maxw or not cur:
                cur = test
            else:
                out.append(cur)
                cur = w_
        out.append(cur)
    lh = int(size * spacing)
    widths = [int(tmp.textlength(l, font=f)) for l in out]
    tw = max(widths) + 20
    th = lh * len(out) + int(size * 0.35)
    img = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, l in enumerate(out):
        x = {'left': 0, 'center': (tw - widths[i]) / 2, 'right': tw - widths[i]}[align]
        if shadow:
            d.text((x + 3, i * lh + 3), l, font=f, fill=(0, 0, 0, 140))
        d.text((x, i * lh), l, font=f, fill=color)
    return img


def pill(text, size=30, fg=WHITE, bg=RED, padx=22, pady=10, weight='Extra'):
    f = font(size, weight)
    tmp = ImageDraw.Draw(Image.new('L', (10, 10)))
    tw = int(tmp.textlength(text, font=f))
    img = Image.new('RGBA', (tw + padx * 2, size + pady * 2 + 6), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, img.width, img.height], fill=bg)
    d.text((padx, pady - 2), text, font=f, fill=fg)
    return img


def silhouette(scale=1.0, color=(150, 162, 182), mark=True):
    w, h = int(220 * scale), int(300 * scale)
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    hr = 52 * scale
    cx = w / 2
    d.ellipse([cx - hr, 20 * scale, cx + hr, 20 * scale + hr * 2], fill=color)
    d.rounded_rectangle([cx - 100 * scale, 140 * scale, cx + 100 * scale, 300 * scale + 60 * scale],
                        int(90 * scale), fill=color)
    if mark:
        f = font(int(64 * scale), 'Black')
        tw = d.textlength('?', font=f)
        d.text((cx - tw / 2, 40 * scale), '?', font=f, fill=NAVY)
    return img


def plane(scale=1.0, color=WHITE):
    w = int(400 * scale)
    img = Image.new('RGBA', (w, w), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = scale
    c = w / 2
    d.rounded_rectangle([c - 22 * s, 30 * s, c + 22 * s, 370 * s], int(22 * s), fill=color)   # fuselage
    d.polygon([(c - 190 * s, 210 * s), (c + 190 * s, 210 * s), (c + 190 * s, 245 * s), (c - 190 * s, 245 * s)], fill=color)
    for ex in (-120, -60, 60, 120):
        d.rounded_rectangle([c + ex * s - 11 * s, 175 * s, c + ex * s + 11 * s, 230 * s], int(8 * s), fill=color)
    d.polygon([(c - 85 * s, 340 * s), (c + 85 * s, 340 * s), (c + 85 * s, 362 * s), (c - 85 * s, 362 * s)], fill=color)
    return img.rotate(-90, resample=Image.BICUBIC)
