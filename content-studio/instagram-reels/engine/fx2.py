"""Realistic on-video UI, v2: karaoke captions, iPhone with lock-screen notification and inbox,
iMessage bubbles with typing dots, broadcast lower-thirds, Reminders-style checklist, cinematic chapters.
Generic UI only: no third-party app logos or branding."""
import math
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import motion as M
from motion import W, H, ORANGE, WHITE, ease_out, ease_back

SF = "/System/Library/Fonts/SFNS.ttf"
SFR = "/System/Library/Fonts/SFNSRounded.ttf"
INK, GREY, LINE = (17, 17, 20), (138, 138, 142), (229, 229, 234)
IOS_BLUE, IOS_BUBBLE = (10, 132, 255), (233, 233, 235)
_cache = {}


def sf(size, weight="Bold", rounded=False):
    k = (size, weight, rounded)
    if k not in _cache:
        f = ImageFont.truetype(SFR if rounded else SF, size)
        f.set_variation_by_name(weight)
        _cache[k] = f
    return _cache[k]


def shadow(im, sprite, x, y, blur=18, off=(0, 10), alpha=150):
    sh = Image.new("RGBA", (sprite.width + blur * 4, sprite.height + blur * 4), (0, 0, 0, 0))
    sh.paste((0, 0, 0, alpha), (blur * 2 + off[0], blur * 2 + off[1]), sprite.getchannel("A"))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    im.alpha_composite(sh, (int(x - blur * 2), int(y - blur * 2)))


def spring(t, k=9.0, damp=5.5):
    """0→1 with a natural overshoot."""
    if t <= 0:
        return 0.0
    return 1 - math.exp(-damp * t) * math.cos(k * t)


# ---------------------------------------------------------------- captions (karaoke)
def _chunks(disp):
    chunks, cur = [], []
    for i, w in enumerate(disp):
        cur.append(i)
        if len(cur) == 3 or w[-1] in ".,?!:" or (len(cur) == 2 and len(w) > 9):
            chunks.append(cur); cur = []
    if cur:
        chunks.append(cur)
    return chunks


def draw_captions(im, ln, t, cy=1030):
    nb, nc = len(ln.words), len(ln.disp)
    if not nb:
        return
    starts = [ln.words[min(nb - 1, int(i * nb / max(1, nc)))][0] + ln.lead for i in range(nc)]
    chunk = None
    for c in _chunks(ln.disp):
        if t >= starts[c[0]] - 0.03:
            chunk = c
    if not chunk:
        return
    f = sf(98, "Black")
    space = f.getlength(" ")
    words = [ln.disp[i].upper() for i in chunk]
    # wrap into max 2 lines within 840px
    lines, cur, cw = [], [], 0
    for wi, w in zip(chunk, words):
        ww = f.getlength(w)
        if cur and cw + space + ww > 840:
            lines.append(cur); cur, cw = [], 0
        cur.append((wi, w)); cw += ww + (space if len(cur) > 1 else 0)
    lines.append(cur)
    lh = 112
    layer = Image.new("RGBA", (W, lh * len(lines) + 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    active = max(i for i in chunk if t >= starts[i] - 0.03) if any(t >= starts[i] - 0.03 for i in chunk) else chunk[0]
    for li, line in enumerate(lines):
        tw = sum(f.getlength(w) for _, w in line) + space * (len(line) - 1)
        x = W / 2 - 60 - tw / 2
        y = 20 + li * lh
        for wi, w in line:
            ww = f.getlength(w)
            st = starts[wi]
            if t < st - 0.03:
                x += ww + space
                continue
            p = ease_out((t - st + 0.03) / 0.12)
            dy = int(18 * (1 - p))
            clean = ln.disp[wi].strip(".,?!:").lower()
            if wi == active:
                pad = 14
                d.rounded_rectangle([x - pad, y + dy - 4, x + ww + pad, y + dy + 104], radius=18, fill=ORANGE + (int(255 * p),))
                col = WHITE
            else:
                col = ORANGE if clean in ln.hi else WHITE
            d.text((x, y + dy), w, font=f, fill=col + (int(255 * p),))
            x += ww + space
    top = int(cy - layer.height / 2)
    shadow(im, layer, 0, top, blur=14, off=(0, 8), alpha=170)
    im.alpha_composite(layer, (0, top))


# ---------------------------------------------------------------- iPhone
PW, PH = 420, 860


def _iphone_frame():
    body = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    # titanium edge: layered rounded rects for a soft metallic gradient
    for i, c in enumerate([(98, 98, 104), (140, 140, 146), (112, 112, 118), (70, 70, 76)]):
        d.rounded_rectangle([i, i, PW - 1 - i, PH - 1 - i], radius=72 - i, fill=c)
    d.rounded_rectangle([6, 6, PW - 7, PH - 7], radius=66, fill=(8, 8, 10))
    return body


FRAME = _iphone_frame()
SCREEN_BOX = (16, 16, PW - 16, PH - 16)


def _screen_mask():
    m = Image.new("L", (PW, PH), 0)
    ImageDraw.Draw(m).rounded_rectangle(SCREEN_BOX, radius=58, fill=255)
    return m


SCREEN_MASK = _screen_mask()


def _wallpaper():
    w, h = PW, PH
    small = Image.new("RGB", (w // 6, h // 6), (16, 22, 44))
    d = ImageDraw.Draw(small)
    d.ellipse([-20, 60, 60, 140], fill=(214, 92, 52))
    d.ellipse([30, -20, 90, 40], fill=(40, 70, 140))
    d.ellipse([10, 100, 80, 160], fill=(30, 40, 90))
    small = small.filter(ImageFilter.GaussianBlur(14))
    return small.resize((w, h), Image.BICUBIC).convert("RGBA")


WALL = _wallpaper()


def _status_bar(d, dark=False):
    col = WHITE if not dark else INK
    d.text((52, 30), "4:55", font=sf(26, "Semibold"), fill=col)
    # signal, wifi, battery
    x = PW - 120
    for i in range(4):
        d.rounded_rectangle([x + i * 9, 48 - i * 5, x + i * 9 + 5, 52], radius=1, fill=col)
    d.rounded_rectangle([PW - 72, 36, PW - 36, 52], radius=5, outline=col, width=2)
    d.rounded_rectangle([PW - 69, 39, PW - 50, 49], radius=3, fill=col)


def _island(d):
    d.rounded_rectangle([PW / 2 - 64, 26, PW / 2 + 64, 64], radius=19, fill=(0, 0, 0))


def _mail_icon(size):
    ic = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(ic)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.24), fill=(40, 140, 250))
    m = size * 0.2
    d.rounded_rectangle([m, size * 0.3, size - m, size * 0.72], radius=3, fill=WHITE)
    d.line([(m, size * 0.32), (size / 2, size * 0.52), (size - m, size * 0.32)], fill=(40, 140, 250), width=max(2, size // 16))
    return ic


MAIL = _mail_icon(64)


def screen_lock(t, notif):
    scr = WALL.copy()
    d = ImageDraw.Draw(scr)
    _status_bar(d)
    _island(d)
    d.text((PW / 2 - sf(24, "Semibold").getlength("Friday, November 6") / 2, 96), "Friday, November 6", font=sf(24, "Semibold"), fill=(235, 235, 240))
    clock = "4:55"
    fc = sf(150, "Bold", rounded=True)
    d.text((PW / 2 - fc.getlength(clock) / 2, 112), clock, font=fc, fill=(245, 245, 250))
    # notification banner drops in
    p = spring((t - 0.55) / 1.0)
    if p > 0:
        title, body = notif
        bx0, bx1 = 26, PW - 26
        by = 330 - (1 - min(p, 1)) * 140 + (p - 1) * 30 if p > 1 else 330 - (1 - p) * 140
        card = Image.new("RGBA", (bx1 - bx0, 156), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, card.width - 1, card.height - 1], radius=30, fill=(245, 245, 247, 236))
        card.alpha_composite(MAIL.resize((52, 52)), (16, 18))
        cd.text((80, 20), "MAIL", font=sf(19, "Semibold"), fill=GREY)
        cd.text((card.width - 60, 20), "now", font=sf(19, "Regular"), fill=GREY)
        cd.text((80, 46), title, font=sf(26, "Semibold"), fill=INK)
        # wrap body to 2 lines
        fb = sf(23, "Regular")
        words, lines, cur = body.split(), [], ""
        for w in words:
            tst = (cur + " " + w).strip()
            if fb.getlength(tst) > card.width - 100 and cur:
                lines.append(cur); cur = w
            else:
                cur = tst
        lines.append(cur)
        for i, l in enumerate(lines[:2]):
            cd.text((80, 80 + i * 30), l, font=fb, fill=(60, 60, 66))
        scr.alpha_composite(card, (bx0, int(by)))
    # flashlight / camera buttons
    for cx in (80, PW - 80):
        d.ellipse([cx - 30, PH - 140, cx + 30, PH - 80], fill=(40, 40, 50, 180))
    d.rounded_rectangle([PW / 2 - 70, PH - 40, PW / 2 + 70, PH - 32], radius=4, fill=(240, 240, 245))
    return scr


def screen_inbox(t, rows, hours):
    scr = Image.new("RGBA", (PW, PH), (255, 255, 255, 255))
    d = ImageDraw.Draw(scr)
    _status_bar(d, dark=True)
    _island(d)
    d.text((34, 82), "‹ Mailboxes", font=sf(22, "Regular"), fill=IOS_BLUE)
    d.text((PW - 70, 82), "Edit", font=sf(22, "Regular"), fill=IOS_BLUE)
    d.text((32, 116), "Shared Inbox", font=sf(42, "Bold"), fill=INK)
    d.rounded_rectangle([32, 176, PW - 32, 212], radius=10, fill=(239, 239, 244))
    d.text((48, 182), "Search", font=sf(21, "Regular"), fill=GREY)
    y = 230
    for i, (sender, subj, prev, when, target) in enumerate(rows):
        a = ease_out((t - 0.15 - i * 0.08) / 0.3)
        if a <= 0:
            continue
        yy = y + i * 118 + int(20 * (1 - a))
        if target:
            pulse = 0.5 + 0.5 * math.sin(t * 5)
            d.rounded_rectangle([12, yy - 6, PW - 12, yy + 108], radius=14, fill=(255, 241, 232) if pulse > 0.3 else (255, 248, 243))
            d.ellipse([16, yy + 14, 28, yy + 26], fill=IOS_BLUE)
        d.text((38, yy + 4), sender, font=sf(25, "Bold" if target else "Semibold"), fill=INK)
        d.text((PW - 34 - sf(20, "Regular").getlength(when), yy + 8), when, font=sf(20, "Regular"), fill=GREY)
        d.text((38, yy + 38), subj, font=sf(22, "Semibold" if target else "Regular"), fill=INK)
        d.text((38, yy + 68), prev, font=sf(20, "Regular"), fill=GREY)
        if target:
            tag = "Unassigned"
            tw = sf(18, "Semibold").getlength(tag)
            d.rounded_rectangle([PW - 52 - tw, yy + 66, PW - 30, yy + 94], radius=14, fill=ORANGE)
            d.text((PW - 41 - tw, yy + 69), tag, font=sf(18, "Semibold"), fill=WHITE)
        d.line([(38, yy + 106), (PW - 16, yy + 106)], fill=LINE, width=2)
    # live "unread for" counter
    h = int(hours * ease_out((t - 0.5) / 2.2))
    box = [28, PH - 170, PW - 28, PH - 70]
    d.rounded_rectangle(box, radius=22, fill=(255, 236, 234))
    d.text((52, PH - 156), "Unread for", font=sf(22, "Semibold"), fill=(200, 60, 50))
    d.text((52, PH - 128), f"{h} hours", font=sf(40, "Heavy"), fill=(214, 48, 40))
    d.rounded_rectangle([PW / 2 - 70, PH - 40, PW / 2 + 70, PH - 32], radius=4, fill=INK)
    return scr


def draw_phone(im, kind, t, cx=700, cy=640, scale=0.86, buzz_at=0.55, **kw):
    if kind == "lock":
        scr = screen_lock(t, kw.get("notif", ("Landscaping Co.", "Quote request: 2 trucks, need coverage by Monday")))
    else:
        scr = screen_inbox(t, kw["rows"], kw.get("hours", 64))
    dev = FRAME.copy()
    dev.paste(scr, (0, 0), SCREEN_MASK)
    dd = ImageDraw.Draw(dev)
    _island(dd)
    # side buttons
    side = Image.new("RGBA", (PW + 12, PH), (0, 0, 0, 0))
    sd = ImageDraw.Draw(side)
    for (y0, y1) in [(170, 230), (250, 330), (345, 425)]:
        sd.rounded_rectangle([0, y0, 8, y1], radius=3, fill=(120, 120, 126))
    sd.rounded_rectangle([PW + 4, 260, PW + 12, 380], radius=3, fill=(120, 120, 126))
    side.alpha_composite(dev, (6, 0))
    p = spring((t - 0.05) / 0.9, k=7.5, damp=6.0)
    if p <= 0.001:
        return
    tilt = -6 * (1 - min(1.0, p)) + 1.8 * math.sin(t * 1.3)
    jitter = 0
    if kind == "lock" and buzz_at <= t <= buzz_at + 0.55:
        jitter = 7 * math.sin((t - buzz_at) * 90)
        tilt += 1.2 * math.sin((t - buzz_at) * 70)
    s = side.resize((int(side.width * scale), int(side.height * scale)), Image.LANCZOS).rotate(tilt, expand=True, resample=Image.BICUBIC)
    x = cx - s.width / 2 + jitter
    y = cy - s.height / 2 + (1 - min(1.2, p)) * 420
    shadow(im, s, x, y, blur=26, off=(10, 26), alpha=160)
    im.alpha_composite(s, (int(x), int(y)))
    if kind == "lock" and buzz_at <= t <= buzz_at + 0.7:
        d = ImageDraw.Draw(im)
        a = int(220 * (1 - (t - buzz_at) / 0.7))
        for k in range(3):
            r = 30 + k * 22
            for side_x, a0, a1 in [(x - 12, 150, 210), (x + s.width + 12, -30, 30)]:
                d.arc([side_x - r, y + 160 - r, side_x + r, y + 160 + r], a0, a1, fill=(255, 255, 255, a), width=5)


# ---------------------------------------------------------------- iMessage bubble
def draw_bubble(im, bubble, t, x=80, y=430):
    who, text = bubble
    d = ImageDraw.Draw(im)
    a0 = ease_out(t / 0.25)
    fw = sf(28, "Semibold")
    d.text((x + 8, y), who, font=fw, fill=(240, 240, 245, int(255 * a0)))
    y2 = y + 46
    if t < 0.75:
        # typing indicator
        p = ease_back(t / 0.3)
        if p <= 0:
            return
        bw, bh = 150, 84
        b = Image.new("RGBA", (bw + 30, bh + 30), (0, 0, 0, 0))
        bd = ImageDraw.Draw(b)
        bd.rounded_rectangle([10, 0, 10 + bw, bh], radius=42, fill=IOS_BUBBLE)
        bd.ellipse([0, bh - 22, 22, bh], fill=IOS_BUBBLE)
        for k in range(3):
            ph = math.sin(t * 9 - k * 0.9)
            c = 150 + int(60 * (ph + 1) / 2)
            bd.ellipse([46 + k * 34 - 9, 33 - 9 - 5 * max(0, ph), 46 + k * 34 + 9, 33 + 9 - 5 * max(0, ph)], fill=(c - 40, c - 40, c - 36))
        b = b.resize((max(1, int(b.width * p)), max(1, int(b.height * p))), Image.BILINEAR)
        shadow(im, b, x, y2, blur=12, off=(0, 6), alpha=90)
        im.alpha_composite(b, (x, y2))
        return
    p = spring((t - 0.75) / 0.6, k=10, damp=7)
    f = sf(44, "Regular")
    words, lines, cur = text.split(), [], ""
    for w in words:
        tst = (cur + " " + w).strip()
        if f.getlength(tst) > 640 and cur:
            lines.append(cur); cur = w
        else:
            cur = tst
    lines.append(cur)
    bw = max(f.getlength(l) for l in lines) + 56
    bh = len(lines) * 56 + 36
    b = Image.new("RGBA", (int(bw) + 30, int(bh) + 10), (0, 0, 0, 0))
    bd = ImageDraw.Draw(b)
    bd.rounded_rectangle([10, 0, 10 + bw, bh], radius=40, fill=IOS_BUBBLE)
    bd.pieslice([0, bh - 34, 34, bh + 2], 90, 180, fill=IOS_BUBBLE)
    for i, l in enumerate(lines):
        bd.text((38, 16 + i * 56), l, font=f, fill=INK)
    sc = max(0.01, min(1.15, p))
    b2 = b.resize((max(1, int(b.width * sc)), max(1, int(b.height * sc))), Image.BILINEAR)
    shadow(im, b2, x, y2, blur=14, off=(0, 8), alpha=110)
    im.alpha_composite(b2, (x, y2))
    if t > 1.4:
        d.text((x + 14, y2 + bh + 14), "Delivered", font=sf(22, "Medium"), fill=(220, 220, 228, int(255 * ease_out((t - 1.4) / 0.3))))


# ---------------------------------------------------------------- broadcast lower-third
def draw_tag(im, tag, t, x=80, y=1160):
    name, role = tag
    fn, fr = sf(50, "Heavy"), sf(30, "Medium")
    w = int(max(fn.getlength(name), fr.getlength(role)) + 74)
    h = 120
    g = ease_out(t / 0.22)
    if g <= 0:
        return
    d = ImageDraw.Draw(im)
    wipe = ease_out((t - 0.12) / 0.35)
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rectangle([0, 0, w, h], fill=(250, 250, 252, 245))
    ty = int(30 * (1 - ease_out((t - 0.25) / 0.3)))
    cd.text((34, 14 + ty), name, font=fn, fill=INK)
    ra = ease_out((t - 0.4) / 0.3)
    cd.text((34, 74), role, font=fr, fill=(110, 110, 118, int(255 * ra)))
    vis = card.crop((0, 0, max(1, int(w * wipe)), h))
    if wipe > 0.01:
        shadow(im, vis, x + 14, y, blur=16, off=(0, 8), alpha=120)
        im.alpha_composite(vis, (x + 14, y))
    d.rectangle([x, y + h * (1 - g), x + 14, y + h], fill=ORANGE)


# ---------------------------------------------------------------- Reminders-style checklist
def draw_checklist(im, title, items, t, x=80, y=300, w=760):
    rowh = 92
    h = 108 + rowh * len(items)
    p = spring(t / 0.7, k=8, damp=6.5)
    if p <= 0.01:
        return
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([0, 0, w - 1, h - 1], radius=34, fill=(255, 255, 255, 248))
    cd.text((36, 26), title, font=sf(44, "Bold"), fill=ORANGE)
    done = sum(1 for i in range(len(items)) if t > 0.9 + i * 0.55)
    cnt = str(done)
    cd.text((w - 40 - sf(44, "Bold").getlength(cnt), 26), cnt, font=sf(44, "Bold"), fill=ORANGE)
    for i, text in enumerate(items):
        ry = 100 + i * rowh
        a = ease_out((t - 0.35 - i * 0.18) / 0.3)
        if a <= 0:
            continue
        cx, cy, r = 62, ry + rowh / 2, 24
        cp = ease_out((t - 0.9 - i * 0.55) / 0.35)
        if cp > 0:
            cd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ORANGE)
            pts = [(cx - 11, cy + 1), (cx - 3, cy + 9), (cx + 12, cy - 9)]
            seg = cp * 2
            if seg <= 1:
                q = (pts[0][0] + (pts[1][0] - pts[0][0]) * seg, pts[0][1] + (pts[1][1] - pts[0][1]) * seg)
                cd.line([pts[0], q], fill=WHITE, width=6)
            else:
                q = (pts[1][0] + (pts[2][0] - pts[1][0]) * (seg - 1), pts[1][1] + (pts[2][1] - pts[1][1]) * (seg - 1))
                cd.line([pts[0], pts[1], q], fill=WHITE, width=6, joint="curve")
        else:
            cd.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(199, 199, 204), width=4)
        cd.text((110, cy - 24 + int(14 * (1 - a))), text, font=sf(40, "Medium"), fill=INK + (int(255 * a),))
        if i < len(items) - 1:
            cd.line([(110, ry + rowh), (w - 30, ry + rowh)], fill=LINE, width=2)
    s = card.resize((max(1, int(w * min(p, 1.05))), max(1, int(h * min(p, 1.05)))), Image.BILINEAR)
    xx = x + (w - s.width) / 2
    yy = y + (h - s.height) / 2
    shadow(im, s, xx, yy, blur=24, off=(0, 14), alpha=140)
    im.alpha_composite(s, (int(xx), int(yy)))


# ---------------------------------------------------------------- cinematic chapter card
def draw_chapter(im, text, t, kicker=None):
    if t > 1.6:
        return
    a = ease_out(t / 0.22) * (1 - ease_out((t - 1.3) / 0.3))
    d = ImageDraw.Draw(im)
    bar = int(330 * a)
    d.rectangle([0, 0, W, bar], fill=(0, 0, 0))
    d.rectangle([0, H - bar, W, H], fill=(0, 0, 0))
    dim = Image.new("RGBA", (W, H), (0, 0, 0, int(120 * a)))
    im.alpha_composite(dim)
    f = sf(118, "Black")
    tw = f.getlength(text)
    cx = W / 2 - 60
    sc = 1.25 - 0.25 * ease_out(t / 0.35)
    lay = Image.new("RGBA", (int(tw) + 40, 160), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((20, 10), text, font=f, fill=WHITE + (int(255 * a),))
    lay = lay.resize((int(lay.width * sc), int(lay.height * sc)), Image.BILINEAR)
    im.alpha_composite(lay, (int(cx - lay.width / 2), int(860 - lay.height / 2)))
    u = ease_out((t - 0.2) / 0.4)
    d.rectangle([cx - tw / 2 * u, 960, cx + tw / 2 * u, 970], fill=ORANGE + (int(255 * a),))
    if kicker:
        fk = sf(34, "Semibold")
        d.text((cx - fk.getlength(kicker) / 2, 740), kicker, font=fk, fill=ORANGE + (int(255 * a),))


# ---------------------------------------------------------------- progress bar with glowing head
def draw_progress(im, frac):
    d = ImageDraw.Draw(im)
    y = 216
    d.rounded_rectangle([40, y, W - 40, y + 6], radius=3, fill=(255, 255, 255, 70))
    xe = 40 + (W - 80) * frac
    d.rounded_rectangle([40, y, xe, y + 6], radius=3, fill=ORANGE)
    g = Image.new("RGBA", (60, 60), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse([18, 18, 42, 42], fill=ORANGE + (200,))
    g = g.filter(ImageFilter.GaussianBlur(7))
    im.alpha_composite(g, (int(xe - 30), y + 3 - 30))
    d.ellipse([xe - 7, y - 4, xe + 7, y + 10], fill=WHITE)
