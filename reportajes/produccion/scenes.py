"""Scene definitions for the Bukele/Haiti special, timed to the Descript composition."""
from gfx import *

# map coordinates (SVG units)
PAP = (656.8, 523.9)      # Puerto Príncipe
CDB = (658.0, 523.3)      # Croix-des-Bouquets
SSV = (524.4, 565.8)      # San Salvador
SDQ = (675.7, 524.6)      # Santo Domingo
WIDE = (600, 540, 300)
HAITI = (660, 522, 46)
ESV = (527, 563, 40)

TOTAL = 928.2
INTRO_END, VO1, VO2, VO3, VO4, VO4_END = 12.0, 12.0, 249.39, 446.63, 669.39, 903.19


class Item:
    """An overlay on the output frame (not affected by Ken Burns)."""
    def __init__(self, img, x, y, t_in, t_out=None, anim='up', dur=0.6):
        self.img, self.x, self.y = img, x, y
        self.t_in, self.t_out, self.anim, self.dur = t_in, t_out, anim, dur
        self.arr = np.array(img.convert('RGBA'))


class Counter:
    """Animated number that counts up."""
    def __init__(self, x, y, t_in, t_dur, v0, v1, fmt, size=220, color=WHITE, align='center', suffix=''):
        self.x, self.y, self.t_in, self.t_dur = x, y, t_in, t_dur
        self.v0, self.v1, self.fmt, self.size, self.color, self.align, self.suffix = v0, v1, fmt, size, color, align, suffix
        self.cache = {}


class Scene:
    def __init__(self, start, end, bg, items=(), kb=(1.0, 1.1), pan=(0, 0)):
        self.start, self.end, self.bg = start, end, bg
        self.items = list(items)
        self.kb, self.pan = kb, pan
        self.bg_arr = None


def centered(img, cy, cx=W / 2):
    return int(cx - img.width / 2), int(cy - img.height / 2)


def C(img, t_in, cy, cx=W / 2, t_out=None, anim='up'):
    x, y = centered(img, cy, cx)
    return Item(img, x, y, t_in, t_out, anim)


def L(img, t_in, x, y, t_out=None, anim='left'):
    return Item(img, int(x), int(y), t_in, t_out, anim)


def kicker(text, t, y=200, cx=W / 2, bg=RED):
    return C(pill(text, 34, bg=bg), t, y, cx)


# ------------------------------------------------------------------ builders
def shade(img, mode):
    a = np.zeros((BH, BW), np.float32)
    if mode == 'left':
        x = np.linspace(0, 1, BW)[None, :]
        a[:] = np.clip(1.25 - x * 2.1, 0, 1) * 215
    elif mode == 'center':
        y = np.linspace(-1, 1, BH)[:, None]
        a[:] = np.clip(1 - np.abs(y) * 1.3, 0, 1) * 175
    ov = Image.new('RGBA', (BW, BH), NAVY + (0,))
    ov.putalpha(Image.fromarray(a.astype(np.uint8)))
    img.alpha_composite(ov)


def map_scene(s, e, view, hl=None, markers=(), arrows=(), items=(), kb=(1.0, 1.1), pan=(0, 0), sh=None):
    img, tp = map_image(*view, highlight=hl or {})
    if sh is None:
        sh = 'left' if items else None
    if sh:
        shade(img, sh)
    for p1, p2, col in arrows:
        draw_arrow(img, tp(*p1), tp(*p2), color=col, width=9)
    for pos, label, col, side in markers:
        draw_marker(img, tp(*pos), label, color=col, side=side, r=11, size=36)
    return Scene(s, e, img, items, kb, pan)


_tex = None


def tex():
    global _tex
    if _tex is None:
        _tex = world_texture()
    return _tex


def card(s, e, items=(), kb=(1.0, 1.06), pan=(0, 0), plain=False):
    return Scene(s, e, base_bg() if plain else tex(), items, kb, pan)


def big(text, t, cy=470, size=150, color=WHITE, weight='Black'):
    return C(text_block(text, size, weight, color, align='center'), t, cy)


def sub(text, t, cy=640, size=48, color=GREY, maxw=1500, weight='Semi'):
    return C(text_block(text, size, weight, color, align='center', maxw=maxw), t, cy)


def bullets(rows, times, x=260, y0=330, gap=104, size=50, color=WHITE, dot=RED):
    out = []
    for i, (r, t) in enumerate(zip(rows, times)):
        im = text_block(r, size, 'Bold', color, maxw=1350)
        canvas = Image.new('RGBA', (im.width + 70, max(im.height, size + 20)), (0, 0, 0, 0))
        d = ImageDraw.Draw(canvas)
        d.rectangle([0, size * 0.3, 22, size * 0.3 + 22], fill=dot)
        canvas.alpha_composite(im, (56, 0))
        out.append(L(canvas, t, x, y0 + i * gap))
    return out


def quote_card(s, e, quote, author, t):
    items = []
    q = text_block('“', 300, 'Black', RED, shadow=False)
    items.append(L(q, t, 170, 120, anim='fade'))
    items.append(C(text_block(quote, 72, 'Bold', WHITE, align='center', maxw=1450, spacing=1.25), t + 0.3, 470))
    items.append(C(text_block('— ' + author, 44, 'Semi', GOLD, align='center'), t + 1.2, 740))
    return card(s, e, items, plain=True)


def chapter(s, e, n, title):
    items = [C(pill('CAPÍTULO %d' % n, 40, bg=RED), s + 0.3, 430),
             C(text_block(title, 96, 'Black', WHITE, align='center', maxw=1600), s + 0.7, 560)]
    return card(s, e, items, kb=(1.0, 1.08))


def silhouettes_card(s, e, title, t, sub_=None, cy=520):
    items = []
    for i in range(4):
        sil = silhouette(1.15)
        items.append(C(sil, t + 0.25 * i, cy, W / 2 + (i - 1.5) * 290, anim='fade'))
    items.append(C(text_block(title, 60, 'Black', WHITE, align='center', maxw=1500), t + 1.2, 230))
    if sub_:
        items.append(sub(sub_, t + 1.8, 800, 40))
    return card(s, e, items, plain=True, kb=(1.0, 1.05))


def bar_chart(s, e, t, bars, title, note=None):
    """bars: [(label, value, color)] horizontal bars with counters."""
    items = [C(text_block(title, 58, 'Black', WHITE, align='center', maxw=1600), t, 190)]
    if note:
        items.append(sub(note, t + 2.4, 270, 36))
    vmax = max(v for _, v, _ in bars)
    gap = 150 if len(bars) > 2 else 190
    for i, (lab, v, col) in enumerate(bars):
        y = 340 + i * gap
        items.append(L(text_block(lab, 36, 'Semi', GREY), t + 0.4 + i * 0.6, 240, y))
        bw = int(1100 * v / vmax)
        bar = Image.new('RGBA', (bw, 64), col + (255,))
        items.append(Item(bar, 240, y + 52, t + 0.6 + i * 0.6, anim='grow', dur=1.2))
        items.append(Counter(240 + bw + 30, y + 84, t + 0.6 + i * 0.6, 1.2, 0, v, '{:,.0f}', size=76,
                             color=WHITE, align='left'))
    return card(s, e, items, plain=True)


def timeline_card(s, e, t, pts, title, times=None):
    items = [C(text_block(title, 56, 'Black', WHITE, align='center', maxw=1600), t, 200)]
    line = Image.new('RGBA', (1500, 8), GREY + (255,))
    items.append(Item(line, 210, 520, t + 0.2, anim='grow', dur=1.5))
    n = len(pts)
    for i, (yr, lab) in enumerate(pts):
        x = 210 + int(1500 * (i + 0.5) / n)
        dot = Image.new('RGBA', (40, 40), (0, 0, 0, 0))
        ImageDraw.Draw(dot).ellipse([0, 0, 39, 39], fill=RED, outline=WHITE, width=4)
        ti = times[i] if times else t + 0.5 + i * 0.5
        items.append(C(dot, ti, 524, x, anim='fade'))
        items.append(C(text_block(yr, 50, 'Black', GOLD, align='center'), ti, 450, x))
        items.append(C(text_block(lab, 30, 'Semi', WHITE, align='center', maxw=300), ti + 0.2, 620, x))
    return card(s, e, items, plain=True)


# ------------------------------------------------------------------ the show
def build():
    S = []
    R, G = RED, GOLD
    # INTRO ------------------------------------------------------------
    S.append(map_scene(0, 12.1, WIDE, {'ht': R, 'sv': G}, kb=(1.0, 1.1), sh='center', items=[
        C(pill('ESPECIAL', 44, bg=R), 0.6, 330),
        C(text_block('BUKELE EN HAITÍ', 150, 'Black', WHITE, align='center'), 1.0, 470),
        C(text_block('TODA LA HISTORIA', 70, 'Extra', GOLD, align='center'), 1.6, 600),
        C(text_block('Desde 2021 hasta el 30 de octubre de 2026', 40, 'Semi', GREY, align='center'), 2.4, 700),
    ]))
    # CAPÍTULO 1 -------------------------------------------------------
    S.append(card(12.1, 23.6, [
        C(pill('CAPÍTULO 1 · LAS RAÍCES', 30, bg=R), 12.3, 170),
        Counter(W / 2, 470, 12.2, 1.0, 0, 12, '{:.0f}', size=300, color=WHITE),
        big('DÍAS', 13.0, 650, 110, GOLD),
        sub('Cuatro miembros de la Fuerza Aérea salvadoreña desaparecidos en Haití', 16.5, 790, 44),
    ], plain=True))
    S.append(silhouettes_card(23.6, 30.4, 'Hoy nadie sabe dónde están', 23.7))
    S.append(map_scene(30.4, 48.6, WIDE, {'ht': R, 'sv': G},
                       markers=[(SSV, 'El Salvador', G, 'below'), (PAP, 'Haití', R, 'right')],
                       arrows=[(SSV, PAP, G)], kb=(1.0, 1.08), items=[
        L(pill('MILES DE SOLDADOS RUMBO AL CARIBE', 32, bg=NAVY2), 33.7, 120, 150),
        L(pill('UN PAÍS SIN ESTADO', 30, bg=R), 41.0, 1300, 560),
        L(pill('UNA GUERRA CONTRA LAS PANDILLAS', 30, bg=(150, 110, 20)), 44.6, 120, 820 - 140),
    ]))
    S.append(timeline_card(48.6, 53.4, 48.7, [('2021', 'Magnicidio'), ('2022', 'Régimen de excepción'),
                                               ('2024', 'Viv Ansanm'), ('2025', 'Llegan los salvadoreños'),
                                               ('2026', 'Emboscada')], 'Esta es la historia completa'))
    S.append(card(53.4, 63.4, [
        kicker('7 DE JULIO DE 2021', 53.6, 230),
        big('MAGNICIDIO', 54.6, 420, 160),
        sub('Un comando armado asesina al presidente de Haití en su residencia', 58.0, 590, 50, WHITE),
    ], plain=True, kb=(1.05, 1.0)))
    S.append(card(63.4, 76.8, [
        big('SIN PRESIDENTE ELECTO', 63.6, 360, 110),
        Counter(W / 2, 560, 64.2, 2.0, 2021, 2026, '{:.0f}', size=200, color=GOLD),
        sub('Pobreza · terremotos · inestabilidad política', 67.5, 720, 46),
    ], plain=True))
    S.append(map_scene(76.8, 97.4, HAITI, {'ht': (44, 78, 122)},
                       markers=[(PAP, 'Puerto Príncipe', R, 'left'), (CDB, 'Croix-des-Bouquets', G, 'right')],
                       kb=(1.0, 1.12), pan=(30, 0), items=[
        L(pill('2021 · SECUESTRO DE MISIONEROS', 30, bg=R), 87.0, 120, 150),
        L(text_block('“Recuerden ese lugar”', 56, 'Italic', GOLD), 92.2, 1150, 800 - 120),
    ]))
    S.append(card(97.4, 114.0, [
        kicker('2024', 97.6, 200),
        big('VIV ANSANM', 98.0, 360, 150, WHITE),
        sub('“Vivir juntos”: la alianza de pandillas rivales', 105.3, 500, 50, GOLD),
        *bullets(['Ataques a cárceles y comisarías', 'Asalto al aeropuerto internacional',
                  'Miles de presos escapan'], [108.0, 109.6, 112.2], x=520, y0=590, gap=90, size=46),
    ], plain=True))
    S.append(card(114.0, 123.9, [
        big('RENUNCIA ARIEL HENRY', 114.2, 420, 100),
        sub('Haití queda en manos de un gobierno de transición', 118.2, 560, 50, WHITE),
    ], plain=True))
    S.append(card(123.9, 132.0, [
        sub('Pandillas controlan alrededor del', 126.2, 280, 50, WHITE),
        Counter(W / 2, 470, 127.6, 2.0, 0, 90, '{:.0f}', size=260, color=R, suffix='%'),
        sub('de Puerto Príncipe (según algunos análisis)', 129.2, 660, 46),
    ], plain=True))
    S.append(card(132.0, 141.0, [
        Counter(W / 2, 430, 132.6, 2.0, 0, 1.5, '{:.1f}', size=260, color=GOLD, suffix=' M'),
        sub('de haitianos desplazados · más de la mitad son niños', 135.0, 620, 50, WHITE),
    ], plain=True))
    S.append(card(141.0, 149.6, [
        kicker('JULIO – SEPTIEMBRE 2026 · ONU', 141.2, 220),
        Counter(W / 2 - 380, 460, 143.5, 1.6, 0, 1000, '+{:,.0f}', size=180, color=R),
        C(text_block('asesinados', 46, 'Semi', WHITE, align='center'), 144.3, 600, W / 2 - 380),
        Counter(W / 2 + 380, 460, 146.0, 1.6, 0, 100, '+{:.0f}', size=180, color=GOLD),
        C(text_block('secuestrados', 46, 'Semi', WHITE, align='center'), 146.8, 600, W / 2 + 380),
    ], plain=True))
    S.append(card(149.6, 154.9, [
        *bullets(['Escuelas cerradas', 'Hospitales atacados', 'Elecciones aplazadas'],
                 [149.7, 151.0, 152.2], x=620, y0=330, gap=120, size=64),
    ], plain=True))
    S.append(map_scene(154.9, 159.6, HAITI, {'ht': R}, kb=(1.0, 1.1), items=[
        L(text_block(['Ese es el Haití al que', 'llegarían los soldados', 'salvadoreños'], 56, 'Black', WHITE), 155.1, 120, 160),
    ]))
    S.append(map_scene(159.6, 165.5, WIDE, {'ht': R, 'sv': G},
                       markers=[(SSV, 'El Salvador', G, 'below'), (PAP, 'Haití', R, 'right')],
                       arrows=[(PAP, SSV, GREY)], kb=(1.1, 1.0), items=[
        L(pill('A 1.500 KM DE DISTANCIA', 32, bg=NAVY2), 160.5, 120, 150),
    ]))
    S.append(map_scene(165.5, 178.4, ESV, {'sv': G}, markers=[(SSV, 'San Salvador', R, 'below')],
                       kb=(1.0, 1.1), items=[
        L(pill('RÉGIMEN DE EXCEPCIÓN', 36, bg=R), 166.0, 120, 150),
        L(text_block(['Garantías constitucionales', 'suspendidas'], 54, 'Black', WHITE), 175.8, 120, 260),
    ]))
    S.append(card(178.4, 190.9, [
        big('DECENAS DE MILES', 182.6, 400, 130, WHITE),
        sub('de detenidos acusados de pertenecer a pandillas', 184.0, 540, 50, GOLD),
        sub('Mara Salvatrucha · Barrio 18', 187.5, 650, 44),
    ], plain=True))
    S.append(card(190.9, 198.6, [
        big('CECOT', 191.0, 420, 200, WHITE),
        sub('Centro de Confinamiento del Terrorismo', 192.5, 580, 52, GOLD),
        sub('Una megacárcel construida para miles de presos', 195.0, 670, 42),
    ], plain=True))
    # homicide drop (qualitative)
    arrow = Image.new('RGBA', (300, 300), (0, 0, 0, 0))
    ImageDraw.Draw(arrow).polygon([(110, 0), (190, 0), (190, 170), (260, 170), (150, 300), (40, 170), (110, 170)], fill=GOLD)
    S.append(card(198.6, 210.4, [
        C(arrow, 198.8, 420, 520, anim='fade'),
        L(text_block(['Caída drástica', 'de los homicidios'], 76, 'Black', WHITE), 199.4, 760, 310),
        L(text_block('Según cifras del gobierno salvadoreño', 38, 'Semi', GREY), 200.5, 760, 520),
    ], plain=True))
    S.append(card(210.4, 215.5, [
        kicker('2024', 210.5, 300, bg=NAVY2),
        big('REELEGIDO', 211.4, 450, 150, WHITE),
        sub('con un respaldo abrumador', 212.5, 590, 52, GOLD),
    ], plain=True))
    S.append(card(215.5, 228.6, [
        C(text_block('EL PRECIO DEL MODELO', 70, 'Black', R, align='center'), 215.6, 220),
        *bullets(['Detenciones arbitrarias', 'Falta de debido proceso', 'Muertes bajo custodia',
                  'Concentración de poder sin contrapesos'], [218.6, 220.6, 222.6, 225.4],
                 x=420, y0=330, gap=100, size=54),
    ], plain=True))
    S.append(map_scene(228.6, 243.4, WIDE, {'ht': R, 'sv': G},
                       markers=[(SSV, 'El Salvador', G, 'below'), (PAP, 'Haití', R, 'right')],
                       arrows=[(SSV, PAP, G)], kb=(1.0, 1.1), items=[
        L(text_block(['Bukele insinúa que', 'podría ayudar a Haití'], 60, 'Black', WHITE), 235.9, 120, 140),
        L(pill('PRONTO TENDRÍA LA OPORTUNIDAD', 30, bg=R), 241.5, 120, 330),
    ]))
    S.append(chapter(243.4, 249.4, 2, 'El Salvador llega a Haití'))
    # CAPÍTULO 2 -------------------------------------------------------
    S.append(card(249.4, 272.2, [
        kicker('30 DE OCTUBRE DE 2024', 249.6, 200),
        big('DECRETO LEGISLATIVO', 250.5, 340, 100),
        sub('Autoriza enviar personal militar a Haití', 254.5, 460, 50, WHITE),
        *bullets(['Apoyo a la misión multinacional encabezada por Kenia',
                  'Tarea principal: evacuaciones médicas',
                  'Válido hasta octubre de 2026'], [259.8, 267.3, 272.3 - 0.1], x=330, y0=560, gap=90, size=44),
    ], plain=True))
    S.append(timeline_card(272.2, 295.2, 272.3, [('ENE 2025', '8 miembros de la Fuerza Aérea'),
                                                 ('FEB 2025', 'Unos 78 militares'),
                                                 ('FEB 2025', '3 helicópteros salvadoreños')],
                                                'Los salvadoreños llegan a Haití', times=[279.6, 284.3, 289.9]))
    S.append(card(295.2, 313.9, [
        C(plane(0.9, WHITE).rotate(20, expand=True), 295.4, 470, 420, anim='fade'),
        L(text_block('Apoyo de Estados Unidos', 64, 'Black', WHITE), 295.6, 760, 260),
        *bullets(['2 helicópteros para evacuar heridos', 'Entrenamiento: 10 pilotos', 'y 4 técnicos de mantenimiento'],
                 [297.3, 301.6, 302.6], x=760, y0=380, gap=90, size=44),
        L(text_block('Lejos de los titulares', 46, 'Italic', GOLD), 309.0, 760, 680),
    ], plain=True))
    S.append(card(313.9, 329.1, [
        sub('La misión keniana no logra frenar a las pandillas', 314.1, 250, 50, WHITE),
        sub('Falta personal · equipo · dinero', 316.9, 340, 44),
        kicker('CONSEJO DE SEGURIDAD DE LA ONU', 319.9, 470, bg=NAVY2),
        big(['FUERZA DE SUPRESIÓN', 'DE PANDILLAS'], 324.2, 640, 92, GOLD),
    ], plain=True))
    S.append(card(329.1, 333.6, [
        sub('Efectivos autorizados sobre el papel', 329.2, 300, 52, WHITE),
        Counter(W / 2, 480, 329.4, 1.8, 0, 5550, '{:,.0f}', size=260, color=WHITE),
    ], plain=True))
    S.append(card(333.6, 342.4, [
        kicker('JUNIO DE 2026', 333.7, 300, bg=NAVY2),
        big(['VISITA DEL SECRETARIO', 'GENERAL DE LA ONU'], 334.4, 470, 80),
        sub('“Un punto de inflexión”', 340.2, 640, 54, GOLD),
    ], plain=True))
    S.append(card(342.4, 350.3, [
        sub('Mandato renovado hasta el', 342.5, 360, 54, WHITE),
        big('31 DE MARZO DE 2027', 346.1, 500, 120, GOLD),
    ], plain=True))
    S.append(bar_chart(350.3, 359.3, 350.4, [('Autorizados', 5550, GREY), ('Efectivos reales (12 de octubre)', 1563, RED)],
                       'Pero la realidad era otra', 'Menos de un tercio de lo previsto'))
    S.append(card(359.3, 375.7, [
        kicker('OCTUBRE DE 2026', 359.4, 250, bg=NAVY2),
        big('NUEVA LEY EN EL SALVADOR', 359.8, 390, 90),
        *bullets(['Participación ampliada un año más', 'Permite enviar personal civil y militar',
                  'según lo que la misión necesite'], [361.0, 367.3, 368.5], x=420, y0=500, gap=86, size=48),
        sub('La puerta para un despliegue mayor ya estaba abierta', 372.1, 800, 44, GOLD),
    ], plain=True))
    S.append(card(375.7, 378.2, [big('SEIS DÍAS DESPUÉS…', 375.8, 500, 120, WHITE)], plain=True, kb=(1.0, 1.1)))
    S.append(map_scene(378.2, 404.3, HAITI, {'ht': (44, 78, 122)},
                       markers=[(PAP, 'Puerto Príncipe', GREY, 'left'), (CDB, 'Croix-des-Bouquets', R, 'right')],
                       kb=(1.0, 1.15), pan=(30, 0), items=[
        L(pill('SÁBADO 18 DE OCTUBRE', 36, bg=R), 378.4, 120, 150),
        L(text_block('Convoy de la Fuerza de Supresión de Pandillas', 44, 'Bold', WHITE, maxw=700), 382.4, 120, 240),
        L(text_block('Cuatro miembros de la Fuerza Aérea Salvadoreña a bordo', 40, 'Semi', GREY, maxw=700), 386.3, 120, 360),
        L(text_block('Ataque con explosivos y fuego', 54, 'Black', GOLD, maxw=700), 396.4, 120, 470),
    ]))
    S.append(silhouettes_card(404.3, 417.0, 'Cuatro aerotécnicos salvadoreños desaparecidos', 404.4,
                              'Ningún grupo reivindica el ataque · Haití confirma el secuestro'))
    S.append(card(417.0, 436.5, [
        big('NO SON TROPAS DE COMBATE', 417.1, 300, 96),
        sub('Según el gobierno de El Salvador', 417.6, 400, 40),
        *bullets(['Técnicos de aviación y pilotos', 'Su trabajo: evacuar heridos',
                  'Algunos medios los describen como soldados', '“Estaban allí para salvar vidas”'],
                 [420.1, 424.8, 427.2, 433.3], x=420, y0=480, gap=86, size=46),
    ], plain=True))
    S.append(card(436.5, 440.63, [
        big('TRES DÍAS SIN NOTICIAS…', 436.6, 480, 110, WHITE),
        sub('…y entonces Bukele habla', 438.4, 620, 54, GOLD),
    ], plain=True, kb=(1.0, 1.1)))
    S.append(chapter(440.63, 446.63, 3, 'La respuesta de Bukele'))
    # CAPÍTULO 3 -------------------------------------------------------
    S.append(card(446.63, 457.0, [
        kicker('MARTES 21 DE OCTUBRE', 446.8, 250),
        big(['BUKELE ANUNCIA', 'UNA OPERACIÓN MILITAR'], 448.9, 470, 100),
        sub('Anuncio a través de sus redes sociales', 450.0, 680, 44),
    ], plain=True))
    S.append(quote_card(457.0, 465.6, 'El ataque de hoy no es nada comparado con lo que está por venir '
                        'si no liberan a los cuatro rehenes vivos.', 'Nayib Bukele', 457.1))
    S.append(card(465.6, 473.9, [
        big('ULTIMÁTUM', 465.7, 380, 140, R),
        sub('Entrega inmediata, con vida y sin daños', 465.9, 530, 54, WHITE),
    ], plain=True))
    S.append(map_scene(473.9, 487.9, HAITI, {'ht': R, 'do': (60, 90, 130)},
                       markers=[(PAP, 'Haití', R, 'left'), (SDQ, 'R. Dominicana', G, 'below')],
                       kb=(1.1, 1.0), items=[
        L(pill('COORDINACIÓN', 34, bg=NAVY2), 474.0, 120, 150),
        L(text_block(['Primer ministro de Haití:', 'Alix Didier Fils-Aimé'], 46, 'Bold', WHITE), 474.5, 120, 240),
        L(text_block(['Presidente dominicano:', 'Luis Abinader'], 46, 'Bold', WHITE), 480.4, 120, 420),
    ]))
    S.append(card(487.9, 496.0, [
        C(plane(0.75, WHITE).rotate(25, expand=True), 488.0, 440, 520, anim='fade'),
        Counter(1150, 410, 488.4, 1.0, 0, 100, '{:.0f}', size=200, color=GOLD, align='left'),
        Counter(1150, 600, 491.9, 1.0, 100, 200, '{:.0f}', size=120, color=WHITE, align='left', suffix=' en total'),
        L(text_block('efectivos de fuerzas especiales · fuente: AP', 34, 'Semi', GREY), 489.0, 1000, 720),
    ], plain=True))
    S.append(card(496.0, 508.8, [
        C(text_block('LAS ADVERTENCIAS', 66, 'Black', R, align='center'), 496.1, 230),
        *bullets(['Haití no es El Salvador', 'Pandillas con fusiles de alto calibre',
                  'Cualquier error lo pagarían los civiles'], [500.5, 504.4, 506.0], x=420, y0=360, gap=110, size=56),
    ], plain=True))
    S.append(card(508.8, 525.4, [
        kicker('JUEVES 23 DE OCTUBRE', 508.9, 220),
        big('“SATÁNICAS”', 512.0, 400, 150, GOLD),
        sub('Así califica Bukele a las pandillas de Haití', 512.5, 540, 50, WHITE),
        sub('Asegura que, en sus palabras, Dios dará la victoria a los salvadoreños', 520.3, 660, 42),
    ], plain=True))
    S.append(quote_card(525.4, 530.3, 'La ONU ha carecido de voluntad política para resolver el problema '
                        'de las pandillas en Haití.', 'Nayib Bukele', 525.5))
    S.append(card(530.3, 539.8, [
        big('CRÍTICA A LA ONU', 530.4, 400, 120),
        sub('…y a la misión de la que forman parte sus propios hombres', 534.3, 540, 50, WHITE),
    ], plain=True))
    S.append(card(539.8, 545.9, [
        Counter(W / 2, 430, 540.0, 1.6, 0, 450, '+{:.0f}', size=260, color=GOLD),
        sub('soldados salvadoreños en Haití, según un diario haitiano', 541.5, 620, 46, WHITE),
    ], plain=True))
    S.append(card(545.9, 561.2, [
        kicker('VIERNES 24 DE OCTUBRE', 546.0, 230),
        big('EL MOMENTO MÁS ANGUSTIOSO', 548.0, 380, 90),
        sub('Entregan restos humanos a los militares salvadoreños en el aeropuerto de Puerto Príncipe',
            550.5, 540, 46, WHITE, maxw=1400),
        sub('Durante horas se teme lo peor', 556.8, 690, 44, GOLD),
    ], plain=True))
    S.append(card(561.2, 575.6, [
        C(text_block('BUKELE: “NO SON ELLOS”', 70, 'Black', WHITE, align='center'), 561.3, 220),
        *bullets(['Un niño', 'Un hombre considerablemente más alto', 'Parte de un uniforme de otro ejército'],
                 [563.0, 564.9, 568.4], x=420, y0=340, gap=105, size=54, dot=GOLD),
        sub('Un funcionario lo confirma después de forma anónima', 570.9, 720, 42),
    ], plain=True))
    S.append(map_scene(575.6, 587.9, HAITI, {'ht': (44, 78, 122)},
                       markers=[(CDB, 'Zona de la emboscada', R, 'right')], kb=(1.0, 1.1), pan=(30, 0), items=[
        L(text_block('“400 Mawozo”', 64, 'Black', GOLD), 579.3, 120, 160),
        L(text_block(['Su líder señalado,', 'Wilson Joseph, niega', 'tener a los rehenes'], 50, 'Bold', WHITE), 581.0, 120, 260),
        L(text_block('Nadie puede confirmar si siguen con vida', 40, 'Semi', GREY, maxw=760), 585.4, 120, 470),
    ]))
    S.append(bar_chart(587.9, 613.9, 588.0, [('Lunes 27 · Reuters', 1000, GREY), ('Martes 28 · otros reportes', 1300, GREY),
                                             ('Miércoles 29 · Reuters', 2000, RED)],
                       'El despliegue se acelera', 'Cancillería salvadoreña: “más de 2.000” miembros de la Fuerza Armada'))
    S.append(bar_chart(613.9, 620.2, 613.95, [('Soldados salvadoreños (29 oct.)', 2000, RED),
                                              ('Fuerza de la ONU completa (12 oct.)', 1563, GREY)],
                       'Para dimensionarlo'))
    S.append(card(620.2, 637.5, [
        C(plane(1.0, WHITE).rotate(15, expand=True), 620.3, 450, 520, anim='fade'),
        L(pill('COMANDO SUR DE EE. UU.', 30, bg=NAVY2), 622.5, 800, 280),
        L(text_block(['Aviones Hércules', 'C-130 para el traslado'], 64, 'Black', WHITE), 622.6, 800, 360),
        L(text_block('Apoyo logístico, no participación en combate', 40, 'Semi', GOLD, maxw=900), 627.8, 800, 560),
        L(text_block('Washington no ha frenado la operación', 40, 'Semi', GREY, maxw=900), 633.1, 800, 650),
    ], plain=True))
    S.append(card(637.5, 650.1, [
        kicker('MIÉRCOLES 29 DE OCTUBRE', 637.6, 260),
        big('“ESTO NO ES UNA INVASIÓN”', 643.3, 430, 100, WHITE),
        sub('Objetivo, según Bukele: rescatar a los suyos y “dar una lección” a las pandillas', 644.9, 580, 46, GOLD),
    ], plain=True))
    S.append(card(650.1, 663.39, [
        kicker('JUEVES 30 DE OCTUBRE', 650.2, 220),
        sub('Bukele asegura que la operación puede acabar con las pandillas de Haití', 652.2, 360, 52, WHITE),
        big(['“Si los entregan vivos,', 'ese mismo día nos regresamos”'], 658.3, 560, 80, GOLD),
    ], plain=True))
    S.append(chapter(663.39, 669.39, 4, 'Las dudas y el día de hoy'))
    # CAPÍTULO 4 -------------------------------------------------------
    S.append(card(669.39, 689.8, [
        sub('Preguntas sin respuesta', 669.5, 200, 46),
        big('1. ¿QUIÉN MANDA?', 674.7, 380, 130, GOLD),
        sub('Las autoridades no han aclarado la cadena de mando', 677.3, 540, 48, WHITE),
        sub('Un analista citado por Reuters cree que parte de las tropas actuará fuera de la misión de la ONU',
            682.3, 680, 42, GREY),
    ], plain=True))
    S.append(card(689.8, 717.3, [
        big('2. ¿CON QUÉ BASE LEGAL?', 689.9, 260, 110, GOLD),
        *bullets(['La ONU permite participar dentro de la Fuerza de Supresión de Pandillas',
                  'No se conoce un acuerdo formal público para este despliegue',
                  'Sin respaldo explícito de la ONU ni del Escudo de las Américas',
                  '“Operación de rescate paralela y unilateral”'], [692.8, 698.8, 704.9, 711.8],
                 x=260, y0=390, gap=100, size=42),
    ], plain=True))
    S.append(card(717.3, 740.6, [
        big('3. ¿Y LOS CIVILES?', 717.4, 260, 120, R),
        *bullets(['Reglas de enfrentamiento no publicadas', 'Experto de la ONU: la situación es volátil',
                  'Vecinos describen una “lluvia de fuego”'], [721.6, 724.8, 732.9], x=360, y0=400, gap=110, size=50),
    ], plain=True))
    S.append(card(740.6, 753.0, [
        big('CONTRATISTAS PRIVADOS', 740.7, 380, 100),
        sub('Ataques con drones contra las pandillas', 742.0, 520, 50, WHITE),
        sub('Su papel no está claro: aumenta la confusión sobre quién hace qué', 747.0, 630, 42, GOLD),
    ], plain=True))
    S.append(map_scene(753.0, 774.6, HAITI, {'ht': (44, 78, 122)}, kb=(1.0, 1.08), items=[
        L(pill('LAS VOCES DE HAITÍ', 34, bg=R), 753.1, 120, 150),
        L(text_block('Sentimientos encontrados', 56, 'Black', WHITE), 754.0, 120, 240),
        L(text_block(['“Ayude a que las pandillas', 'dejen de aterrorizar', 'a la población”'], 50, 'Italic', GOLD), 761.0, 120, 360),
        L(text_block('Que alguien actúe en días llama la atención', 40, 'Semi', GREY, maxw=820), 768.2, 120, 580),
    ]))
    S.append(card(774.6, 790.5, [
        big('HAITÍ TIENE MEMORIA', 774.7, 360, 110),
        sub('Las intervenciones extranjeras del pasado dejaron heridas profundas', 777.1, 500, 48, WHITE),
        sub('Algunos críticos hablan de una intervención ilegal', 781.3, 610, 44, GOLD),
    ], plain=True))
    S.append(card(790.5, 802.5, [
        kicker('EN EL SALVADOR', 790.6, 230, bg=NAVY2),
        Counter(W / 2, 450, 794.6, 1.6, 0, 68, '{:.0f}', size=260, color=GOLD, suffix='%'),
        sub('respalda mantener o aumentar la participación en Haití', 796.0, 620, 48, WHITE),
        sub('Sondeo citado por la prensa, sin metodología publicada', 798.0, 710, 36),
    ], plain=True))
    S.append(card(802.5, 825.9, [
        kicker('HOY, 30 DE OCTUBRE · DÍA 12', 802.6, 190),
        C(text_block('LO QUE SABEMOS', 70, 'Black', GOLD, align='center'), 806.8, 290),
        *bullets(['18 oct.: cuatro aerotécnicos capturados en Croix-des-Bouquets',
                  'Unos 2.000 soldados salvadoreños en Haití',
                  'Los restos del día 24 no eran los suyos',
                  'Bukele promete retirar las tropas si vuelven con vida'], [808.6, 813.8, 817.2, 820.9],
                 x=240, y0=380, gap=96, size=42, dot=GOLD),
    ], plain=True))
    S.append(silhouettes_card(825.9, 840.4, 'LO QUE NO SABEMOS', 825.95,
                              'Dónde están · quién los tiene · si siguen con vida · bajo qué mando · cuánto tiempo'))
    S.append(card(840.4, 843.1, [big('¿QUÉ PUEDE PASAR?', 840.45, 500, 120, WHITE)], plain=True, kb=(1.0, 1.1)))
    S.append(card(843.1, 873.2, [
        *bullets(['Rescate con vida: enorme victoria política para Bukele',
                  'Fracaso o víctimas civiles: presión internacional sobre San Salvador',
                  'Las tropas se quedan: presencia militar prolongada'], [843.2, 853.6, 862.4],
                 x=200, y0=330, gap=150, size=50),
    ], plain=True))
    S.append(timeline_card(873.2, 881.8, 873.25, [('2021', 'Magnicidio'), ('2022–2024', 'Pandillas y modelo Bukele'),
                                                  ('18 OCT', 'Emboscada'), ('HOY', 'Día 12')], 'Dos historias que se cruzan'))
    S.append(map_scene(881.8, 903.19, HAITI, {'ht': (44, 78, 122)},
                       markers=[(CDB, 'Croix-des-Bouquets', R, 'right')], kb=(1.0, 1.14), pan=(30, 0), items=[
        L(text_block(['¿La operación que cambie Haití…', 'o una guerra más?'], 60, 'Black', WHITE), 894.6, 120, 160),
    ]))
    # OUTRO ------------------------------------------------------------
    S.append(map_scene(903.19, 913.2, WIDE, {'ht': R, 'sv': G}, kb=(1.1, 1.0), sh='center', items=[
        C(text_block('SEGUIREMOS INFORMANDO', 120, 'Black', WHITE, align='center'), 903.4, 500),
        C(pill('BUKELE EN HAITÍ · ESPECIAL', 34, bg=R), 904.2, 640),
    ]))
    S.append(card(913.2, TOTAL + 0.1, [
        C(text_block('FUENTES', 60, 'Black', GOLD, align='center'), 913.3, 260),
        C(text_block(['Reuters · AP · NPR · CNN · Al Jazeera · The Washington Post',
                      'Infobae · The Haitian Times · ONU · OIM · CFR'], 44, 'Semi', WHITE,
                     align='center', spacing=1.5), 913.8, 450),
        C(text_block('Información actualizada al 30 de octubre de 2026', 40, 'Semi', GREY, align='center'), 914.5, 640),
        C(text_block('Gráficos y mapas ilustrativos', 32, 'Reg', GREY, align='center'), 915.0, 720),
    ], plain=True))
    return S


LOWER_THIRDS = [
    (53.6, 'ASESINADO EL PRESIDENTE JOVENEL MOÏSE', '7 de julio de 2021'),
    (81.5, 'SECUESTRO DE MISIONEROS EN CROIX-DES-BOUQUETS', 'Octubre de 2021'),
    (97.4, 'NACE LA ALIANZA DE PANDILLAS “VIV ANSANM”', '2024'),
    (132.0, 'CERCA DE 1,5 MILLONES DE DESPLAZADOS', 'Fuente: OIM'),
    (165.5, 'EL SALVADOR DECRETA EL RÉGIMEN DE EXCEPCIÓN', 'Marzo de 2022'),
    (249.6, 'EL SALVADOR APRUEBA ENVIAR MILITARES A HAITÍ', '30 de octubre de 2024'),
    (279.6, 'LLEGAN PILOTOS, TÉCNICOS Y HELICÓPTEROS SALVADOREÑOS', '2025'),
    (352.1, 'FUERZA DE LA ONU: 1.563 DE 5.550 EFECTIVOS', '12 de octubre de 2026'),
    (378.4, 'EMBOSCADA EN CROIX-DES-BOUQUETS', 'Sábado 18 de octubre'),
    (404.3, 'CUATRO AEROTÉCNICOS SALVADOREÑOS, DESAPARECIDOS', 'Paradero desconocido'),
    (446.8, 'BUKELE ANUNCIA UNA OPERACIÓN MILITAR', 'Martes 21 de octubre'),
    (545.9, 'ENTREGAN RESTOS HUMANOS EN EL AEROPUERTO', 'Viernes 24 de octubre'),
    (581.0, 'WILSON JOSEPH NIEGA TENER A LOS REHENES', 'Banda 400 Mawozo'),
    (601.7, 'CERCA DE 2.000 SOLDADOS SALVADOREÑOS EN HAITÍ', 'Según Reuters · 29 de octubre'),
    (674.7, '¿QUIÉN DIRIGE LA OPERACIÓN?', 'Cadena de mando sin aclarar'),
    (757.3, 'PIERRE ESPÉRANCE', 'Red Nacional de Defensa de los Derechos Humanos'),
    (802.6, 'HOY, 30 DE OCTUBRE — DÍA 12', 'Situación en desarrollo'),
    (827.0, 'PARADERO DE LOS CUATRO SALVADOREÑOS: DESCONOCIDO', 'Sin confirmación oficial'),
]

TICKER = ('ÚLTIMA HORA  ·  El Salvador tiene cerca de 2.000 soldados en Haití, según Reuters  ·  '
          'Cuatro aerotécnicos salvadoreños siguen desaparecidos desde el 18 de octubre  ·  '
          'Bukele: “Esto no es una invasión”  ·  La fuerza de la ONU contaba con 1.563 de 5.550 efectivos autorizados  ·  '
          'El Comando Sur de EE. UU. facilitó aviones de transporte  ·  '
          'Los restos entregados el 24 de octubre no corresponden a los rehenes  ·  '
          'Mandato de la fuerza internacional renovado hasta marzo de 2027  ·  ')
