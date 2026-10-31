"""Generic animated phone screens for the hooks: order tracker, package map, envelope status, and an untracked quote.
No third-party logos or trade dress: Mopshy colors, generic labels."""
import math
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from motion import ORANGE, WHITE, ease_out, ease_back

NEXT = "/System/Library/Fonts/Avenir Next.ttc"
EMOJI = "/System/Library/Fonts/Apple Color Emoji.ttc"
INK, SCREEN, CARD, MUTED, GREEN, RED = (14, 16, 24), (246, 247, 250), (255, 255, 255), (130, 136, 150), (34, 170, 96), (226, 72, 60)
PW, PH = 360, 700
_f = {}


def F(size, idx=5):
    k = (size, idx)
    if k not in _f:
        _f[k] = ImageFont.truetype(NEXT, size, index=idx)
    return _f[k]


def emoji(ch, size):
    f = ImageFont.truetype(EMOJI, 160)
    im = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((20, 20), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)


EMO = {}


def _phone():
    im = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, PW - 1, PH - 1], radius=54, fill=INK)
    d.rounded_rectangle([12, 12, PW - 13, PH - 13], radius=44, fill=SCREEN)
    d.rounded_rectangle([PW / 2 - 52, 24, PW / 2 + 52, 50], radius=13, fill=INK)  # notch
    d.text((34, 26), "9:41", font=F(22, 0), fill=INK)
    return im, d


def _check(d, cx, cy, r, col):
    d.line([(cx - r * 0.45, cy), (cx - r * 0.1, cy + r * 0.38), (cx + r * 0.5, cy - r * 0.35)], fill=col, width=max(3, int(r * 0.3)), joint="curve")


def screen_tracker(t, emo):
    """Delivery-style progress tracker (pizza or envelope)."""
    im, d = _phone()
    title, eta, stages = emo
    d.text((30, 78), title, font=F(30, 0), fill=INK)
    d.text((30, 118), eta, font=F(24, 5), fill=MUTED)
    ch = {"pizza": "🍕", "envelope": "✉️"}[stages[0]]
    if ch not in EMO:
        EMO[ch] = emoji(ch, 120)
    e = EMO[ch]
    bob = int(6 * math.sin(t * 5))
    im.alpha_composite(e, (int(PW / 2 - e.width / 2), 170 + bob))
    steps = stages[1]
    prog = ease_out((t - 0.4) / 1.4) * (len(steps) - 2)
    y0, step_h = 326, 70
    x = 58
    d.line([(x, y0), (x, y0 + step_h * (len(steps) - 1))], fill=(220, 222, 228), width=8)
    d.line([(x, y0), (x, y0 + step_h * prog)], fill=ORANGE, width=8)
    for i, s in enumerate(steps):
        y = y0 + step_h * i
        on = prog >= i - 0.02
        r = 18
        if on:
            d.ellipse([x - r, y - r, x + r, y + r], fill=ORANGE)
            _check(d, x, y, r, CARD)
        else:
            d.ellipse([x - r, y - r, x + r, y + r], fill=SCREEN, outline=(200, 202, 210), width=4)
        d.text((x + 36, y - 16), s, font=F(26, 2 if on else 5), fill=INK if on else MUTED)
    d.rounded_rectangle([24, PH - 120, PW - 24, PH - 40], radius=20, fill=(255, 238, 228))
    d.text((44, PH - 102), "Live updates on", font=F(24, 2), fill=ORANGE)
    return im


def screen_map(t):
    im, d = _phone()
    d.text((30, 78), "Arriving today", font=F(30, 0), fill=INK)
    d.text((30, 118), "Your package · 3 stops away", font=F(22, 5), fill=MUTED)
    # map
    mx0, my0, mx1, my1 = 24, 160, PW - 24, 520
    d.rounded_rectangle([mx0, my0, mx1, my1], radius=22, fill=(232, 236, 242))
    for i in range(6):
        y = my0 + 30 + i * 60
        d.line([(mx0, y), (mx1, y + 20)], fill=(250, 251, 253), width=10)
    for i in range(4):
        x = mx0 + 40 + i * 85
        d.line([(x, my0), (x - 20, my1)], fill=(250, 251, 253), width=10)
    route = [(70, 480), (110, 400), (200, 380), (230, 300), (300, 260), (290, 200)]
    d.line(route, fill=ORANGE, width=8, joint="curve")
    # home pin
    hx, hy = route[-1]
    d.ellipse([hx - 16, hy - 16, hx + 16, hy + 16], fill=INK)
    d.ellipse([hx - 6, hy - 6, hx + 6, hy + 6], fill=CARD)
    # moving van dot
    p = min(0.999, ease_out((t - 0.3) / 2.4) * 0.85)
    seg = p * (len(route) - 1)
    i = int(seg)
    f = seg - i
    vx = route[i][0] + (route[i + 1][0] - route[i][0]) * f
    vy = route[i][1] + (route[i + 1][1] - route[i][1]) * f
    pr = 26 + 6 * math.sin(t * 6)
    d.ellipse([vx - pr, vy - pr, vx + pr, vy + pr], fill=(255, 210, 190))
    d.ellipse([vx - 15, vy - 15, vx + 15, vy + 15], fill=ORANGE, outline=CARD, width=4)
    d.rounded_rectangle([24, 548, PW - 24, 640], radius=20, fill=CARD)
    if "📦" not in EMO:
        EMO["📦"] = emoji("📦", 54)
    im.alpha_composite(EMO["📦"], (40, 566))
    d.text((110, 562), "Out for delivery", font=F(24, 2), fill=INK)
    d.text((110, 596), "Arrives by 2:40pm", font=F(22, 5), fill=GREEN)
    return im


def screen_unknown(t):
    im, d = _phone()
    d.text((30, 78), "Quote request", font=F(30, 0), fill=INK)
    d.text((30, 118), "Commercial auto · example", font=F(22, 5), fill=MUTED)
    d.rounded_rectangle([24, 170, PW - 24, 400], radius=22, fill=CARD)
    d.text((48, 192), "Status", font=F(22, 5), fill=MUTED)
    q = 1 + 0.08 * math.sin(t * 6)
    fq = F(int(96 * q), 0)
    d.text((48, 228), "???", font=fq, fill=(170, 172, 182))
    d.text((48, 340), "Owner: unassigned", font=F(22, 2), fill=RED)
    rows = [("Last touched", "6 days ago"), ("Follow-up sent", "No"), ("Docs received", "1 of 3")]
    for i, (k, v) in enumerate(rows):
        y = 430 + i * 62
        d.text((34, y), k, font=F(22, 5), fill=MUTED)
        d.text((PW - 34 - F(22, 2).getlength(v), y), v, font=F(22, 2), fill=RED if i < 2 else INK)
    # a notification that never comes
    a = ease_out((t - 0.6) / 0.4)
    if a > 0:
        d.rounded_rectangle([24, PH - 112, PW - 24, PH - 40], radius=20, fill=(255, 232, 230))
        d.text((44, PH - 96), "No updates", font=F(24, 2), fill=RED)
    return im


def draw_widget(frame, kind, t, x, y, scale=1.0):
    if kind == "pizza":
        scr = screen_tracker(t, ("Your order", "On the way · 12 min", ("pizza", ["Ordered", "In the oven", "On the way", "Delivered"])))
    elif kind == "envelope":
        scr = screen_tracker(t, ("Your envelope", "Out for delivery", ("envelope", ["Picked up", "In transit", "Out for delivery", "Delivered"])))
    elif kind == "package":
        scr = screen_map(t)
    else:
        scr = screen_unknown(t)
    a = ease_back((t - 0.15) / 0.45)
    if a <= 0:
        return
    sc = scale * (0.6 + 0.4 * a)
    tilt = 4 * math.sin(t * 1.6) - 3
    s = scr.resize((int(PW * sc), int(PH * sc)), Image.LANCZOS).rotate(tilt, expand=True, resample=Image.BICUBIC)
    shadow = Image.new("RGBA", (s.width + 80, s.height + 80), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 150), (40, 50), s.getchannel("A"))
    shadow = shadow.filter(ImageFilter.GaussianBlur(24))
    slide = int(260 * (1 - ease_out((t - 0.15) / 0.45)))
    fy = int(8 * math.sin(t * 2.4))
    frame.alpha_composite(shadow, (int(x - s.width / 2 - 40 + slide), int(y - s.height / 2 - 40 + fy)))
    frame.alpha_composite(s, (int(x - s.width / 2 + slide), int(y - s.height / 2 + fy)))
