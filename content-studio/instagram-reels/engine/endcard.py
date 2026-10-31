"""Animated Mopshy AI logo end card with a 'Comment KEYWORD' CTA. Logo redrawn as vectors from assets/brand/mopshy-logo-icon.png."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import motion as M
from motion import W, H, FPS, ease_out, ease_back

LOGO_NAVY, LOGO_ORANGE, LOGO_WHITE = (2, 18, 51), (254, 100, 2), (254, 254, 254)
NEXT = "/System/Library/Fonts/Avenir Next.ttc"
EMOJI = "/System/Library/Fonts/Apple Color Emoji.ttc"

# logo geometry in the 1254px source
C = (627, 612)
NODES = [((627, 247), LOGO_ORANGE), ((923, 423), LOGO_WHITE), ((925, 792), LOGO_ORANGE),
         ((627, 962), LOGO_WHITE), ((329, 792), LOGO_ORANGE), ((331, 423), LOGO_WHITE)]
EDGES = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)]
S = 2  # supersample


def draw_logo(t, size):
    """Logo at progress t (seconds into the card), returned as an RGBA sprite of `size` px."""
    big = 1254
    k = S * size / big
    im = Image.new("RGBA", (int(big * k), int(big * k)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    def P(p):
        return (p[0] * k, p[1] * k)
    # tile
    tile = ease_back(t / 0.35)
    if tile <= 0:
        return im.resize((size, size), Image.LANCZOS)
    m = big * (1 - tile) / 2
    d.rounded_rectangle([(8 + m) * k, (8 + m) * k, (1246 - m) * k, (1246 - m) * k], radius=300 * k * max(tile, 0.1), fill=LOGO_NAVY)
    lw = int(13 * k)
    # spokes and edges draw outward
    sp = ease_out((t - 0.25) / 0.45)
    for (p, _) in NODES:
        x = C[0] + (p[0] - C[0]) * sp
        y = C[1] + (p[1] - C[1]) * sp
        if sp > 0:
            d.line([P(C), P((x, y))], fill=LOGO_WHITE, width=lw)
    ep = ease_out((t - 0.55) / 0.45)
    for a, b in EDGES:
        if ep > 0:
            pa, pb = NODES[a][0], NODES[b][0]
            d.line([P(pa), P((pa[0] + (pb[0] - pa[0]) * ep, pa[1] + (pb[1] - pa[1]) * ep))], fill=LOGO_WHITE, width=lw)
    # nodes pop in one by one
    for i, (p, col) in enumerate(NODES):
        q = ease_back((t - 0.6 - i * 0.07) / 0.3)
        if q > 0:
            r = 56 * q
            d.ellipse([P((p[0] - r, p[1] - r)), P((p[0] + r, p[1] + r))], fill=col)
    # center ring
    q = ease_back((t - 0.35) / 0.4)
    if q > 0:
        ro, ri, rd = 134 * q, 86 * q, 50 * q
        d.ellipse([P((C[0] - ro, C[1] - ro)), P((C[0] + ro, C[1] + ro))], fill=LOGO_ORANGE)
        d.ellipse([P((C[0] - ri, C[1] - ri)), P((C[0] + ri, C[1] + ri))], fill=LOGO_NAVY)
        d.ellipse([P((C[0] - rd, C[1] - rd)), P((C[0] + rd, C[1] + rd))], fill=LOGO_WHITE)
    return im.resize((size, size), Image.LANCZOS)


def _emoji(ch, size):
    f = ImageFont.truetype(EMOJI, 160)
    im = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((20, 20), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)


POINT = _emoji("👇", 64)


class EndCard:
    """Behaves like a motion4.Line for timing/audio, but draws the logo card."""
    def __init__(self, keyword, sub="Free workflow review · link in bio", dur=3.4):
        self.keyword, self.sub = keyword, sub
        self.dur, self.lead = dur, 0.0
        self.audio = np.zeros(1, np.float32)
        self.shots, self.tracker, self.timeline, self.endcard = [None], None, None, True

    def frame(self, t, gt):
        im = M.background(gt)
        # pulse rings behind the logo
        cx, cy = W // 2 - 40, 640
        for i in range(2):
            pt = t - 1.0 - i * 0.45
            if 0 < pt < 1.2:
                r = 230 + 260 * ease_out(pt / 1.2)
                a = int(150 * (1 - pt / 1.2))
                ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ImageDraw.Draw(ring).ellipse([cx - r, cy - r, cx + r, cy + r], outline=LOGO_ORANGE + (a,), width=6)
                im.alpha_composite(ring)
        # soft glow + logo, gentle float
        size = 440
        logo = draw_logo(t, size)
        float_y = int(8 * math.sin(gt * 2.2)) if t > 1.2 else 0
        glow = Image.new("RGBA", (size + 160, size + 160), (0, 0, 0, 0))
        ImageDraw.Draw(glow).rounded_rectangle([80, 80, size + 80, size + 80], radius=110, fill=LOGO_ORANGE + (int(110 * ease_out((t - 0.8) / 0.6)),))
        glow = glow.filter(ImageFilter.GaussianBlur(40))
        im.alpha_composite(glow, (cx - size // 2 - 80, cy - size // 2 - 80 + float_y))
        im.alpha_composite(logo, (cx - size // 2, cy - size // 2 + float_y))
        d = ImageDraw.Draw(im)
        # wordmark: "MOPSHY" white + "AI" orange
        q = ease_out((t - 1.05) / 0.35)
        if q > 0:
            f = ImageFont.truetype(NEXT, 104, index=8)
            w1, w2 = f.getlength("MOPSHY "), f.getlength("AI")
            x = cx - (w1 + w2) / 2
            y = 905 + int(40 * (1 - q))
            col = M.mix(M.BG, LOGO_WHITE, q)
            d.text((x, y), "MOPSHY ", font=f, fill=col)
            d.text((x + w1, y), "AI", font=f, fill=M.mix(M.BG, LOGO_ORANGE, q))
        # CTA pill: Comment KEYWORD
        q = ease_back((t - 1.45) / 0.4)
        if q > 0:
            fk = ImageFont.truetype(NEXT, 70, index=8)
            fc = ImageFont.truetype(NEXT, 46, index=2)
            label, kw = "COMMENT", self.keyword.upper()
            pw = fc.getlength(label) + 26 + fk.getlength(kw) + 80
            ph = 124
            pulse = 1.0 + (0.035 * math.sin((t - 1.85) * 7) if t > 1.85 else 0)
            sc = q * pulse
            pill = Image.new("RGBA", (int(pw) + 20, ph + 20), (0, 0, 0, 0))
            pd = ImageDraw.Draw(pill)
            pd.rounded_rectangle([10, 10, 10 + pw, 10 + ph], radius=ph // 2, fill=LOGO_ORANGE)
            pd.text((50, 10 + ph / 2 - fc.size * 0.62), label, font=fc, fill=LOGO_NAVY)
            pd.text((50 + fc.getlength(label) + 26, 10 + ph / 2 - fk.size * 0.66), kw, font=fk, fill=LOGO_WHITE)
            pill = pill.resize((max(1, int(pill.width * sc)), max(1, int(pill.height * sc))), Image.BILINEAR)
            px, py = int(cx - pill.width / 2), int(1100 + (ph + 20) / 2 - pill.height / 2)
            im.alpha_composite(pill, (max(0, px), py))
            # pointing emoji bobbing below the pill
            if t > 1.8:
                by = int(1246 + 8 * math.sin(t * 8))
                im.alpha_composite(POINT, (cx - POINT.width // 2, by))
        q = ease_out((t - 1.9) / 0.4)
        if q > 0:
            fs = ImageFont.truetype(NEXT, 40, index=5)
            d = ImageDraw.Draw(im)
            d.text((cx - fs.getlength(self.sub) / 2, 1392), self.sub, font=fs, fill=M.mix(M.BG, (200, 200, 210), q))
        return im
