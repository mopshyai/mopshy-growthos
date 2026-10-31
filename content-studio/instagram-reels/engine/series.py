"""Story-series layer for motion4: opening sting, progress bar, name tags, text bubbles, chapter cards, illustrative label."""
import math
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
import motion as M
import motion4 as M4
from motion import W, H, ORANGE, WHITE, ease_out, ease_back
from endcard import draw_logo, LOGO_ORANGE

NEXT = "/System/Library/Fonts/Avenir Next.ttc"
NAVY = (14, 18, 30)


def F(size, idx=8):
    return ImageFont.truetype(NEXT, size, index=idx)


class StingCard:
    """1.6s series opener: 'AGENCY RESCUE · EP n' with the logo mark."""
    def __init__(self, series, ep, title, dur=1.6):
        self.series, self.ep, self.title, self.dur, self.lead = series, ep, title, dur, 0.0
        self.audio = np.zeros(1, np.float32)
        self.shots, self.tracker, self.timeline, self.endcard = [None], None, None, True

    def frame(self, t, gt):
        im = M.background(gt)
        d = ImageDraw.Draw(im)
        logo = draw_logo(1.6 + t, 150)
        q = ease_back(t / 0.3)
        if q > 0:
            l2 = logo.resize((max(1, int(150 * q)), max(1, int(150 * q))), Image.LANCZOS)
            im.alpha_composite(l2, (W // 2 - 40 - l2.width // 2, 560 - l2.height // 2))
        a = ease_out((t - 0.15) / 0.3)
        f1, f2, f3 = F(92), F(54, 2), F(44, 5)
        s = self.series.upper()
        x = W // 2 - 40 - f1.getlength(s) / 2
        d.text((x, 680 + 30 * (1 - a)), s, font=f1, fill=M.mix(M.BG, WHITE, a))
        b = ease_out((t - 0.35) / 0.3)
        ep = f"EPISODE {self.ep}"
        d.rounded_rectangle([W // 2 - 40 - f2.getlength(ep) / 2 - 26, 830, W // 2 - 40 + f2.getlength(ep) / 2 + 26, 908],
                            radius=39, fill=M.mix(M.BG, ORANGE, b))
        d.text((W // 2 - 40 - f2.getlength(ep) / 2, 838), ep, font=f2, fill=M.mix(M.BG, NAVY, b))
        c = ease_out((t - 0.55) / 0.3)
        d.text((W // 2 - 40 - f3.getlength(self.title) / 2, 950), self.title, font=f3, fill=M.mix(M.BG, (215, 215, 222), c))
        # sweep line
        sw = ease_out((t - 0.1) / 0.6)
        d.rectangle([W // 2 - 40 - 300 * sw, 1030, W // 2 - 40 + 300 * sw, 1036], fill=LOGO_ORANGE)
        return im


def glass_pill(im, box, radius, alpha=150):
    x0, y0, x1, y1 = [int(v) for v in box]
    reg = im.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(14))
    reg = Image.alpha_composite(reg.convert("RGBA"), Image.new("RGBA", reg.size, (8, 10, 18, alpha)))
    m = Image.new("L", reg.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, reg.width - 1, reg.height - 1], radius=radius, fill=255)
    im.paste(reg, (x0, y0), m)


def draw_tag(im, tag, t):
    name, role = tag
    a = ease_out(t / 0.35)
    if a <= 0:
        return
    fn, fr = F(52), F(32, 2)
    w = max(fn.getlength(name), fr.getlength(role)) + 70
    x = 80 - (1 - a) * 300
    y = 1150
    glass_pill(im, (x, y, x + w, y + 128), 26, 170)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x, y, x + 10, y + 128], radius=5, fill=ORANGE)
    d.text((x + 34, y + 12), name, font=fn, fill=ORANGE)
    d.text((x + 34, y + 76), role, font=fr, fill=(225, 225, 232))


def draw_bubble(im, bubble, t):
    who, text = bubble
    a = ease_back((t - 0.25) / 0.35)
    if a <= 0:
        return
    f, fw = F(56, 5), F(34, 2)
    lines, cur = [], ""
    for wd in text.split():
        test = (cur + " " + wd).strip()
        if f.getlength(test) > 700 and cur:
            lines.append(cur); cur = wd
        else:
            cur = test
    lines.append(cur)
    bw = max(f.getlength(l) for l in lines) + 64
    bh = len(lines) * 72 + 44
    spr = Image.new("RGBA", (int(bw) + 20, int(bh) + 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(spr)
    d.text((14, 0), who, font=fw, fill=(235, 235, 240))
    d.rounded_rectangle([10, 44, 10 + bw, 44 + bh], radius=34, fill=(236, 237, 242))
    d.polygon([(26, 44 + bh - 30), (8, 44 + bh + 8), (56, 44 + bh - 6)], fill=(236, 237, 242))
    for i, l in enumerate(lines):
        d.text((42, 64 + i * 72), l, font=f, fill=(20, 22, 30))
    s = spr.resize((max(1, int(spr.width * a)), max(1, int(spr.height * a))), Image.BILINEAR)
    sh = Image.new("RGBA", (s.width + 60, s.height + 60), (0, 0, 0, 0))
    sh.paste((0, 0, 0, 140), (30, 38), s.getchannel("A"))
    sh = sh.filter(ImageFilter.GaussianBlur(16))
    im.alpha_composite(sh, (80 - 30, 520 - 30))
    im.alpha_composite(s, (80, 520))


def draw_chapter(im, text, t):
    # full-width band for the first 1.1s of the line
    if t > 1.5:
        return
    a = ease_out(t / 0.12) * (1 - ease_out((t - 1.25) / 0.25))
    band = Image.new("RGBA", (W, 300), (255, 101, 49, int(255 * a)))
    im.alpha_composite(band, (0, 700))
    f = F(120)
    d = ImageDraw.Draw(im)
    x = W / 2 - 75 - f.getlength(text) / 2 + (1 - ease_out(t / 0.3)) * 120
    d.text((x, 770), text, font=f, fill=M.mix((255, 101, 49), WHITE, a), stroke_width=4, stroke_fill=M.mix((255, 101, 49), NAVY, a))


def draw_progress(im, frac):
    d = ImageDraw.Draw(im)
    d.rectangle([0, 214, W, 220], fill=(255, 255, 255, 50))
    d.rectangle([0, 214, int(W * frac), 220], fill=ORANGE)


def draw_label(im, gt):
    if gt > 5.5:
        return
    a = min(1.0, gt / 0.4) * (1 - ease_out((gt - 5.0) / 0.5))
    f = F(28, 2)
    txt = "ILLUSTRATIVE STORY · COMPOSITE AGENCY"
    glass_pill(im, (80, 236, 80 + f.getlength(txt) + 40, 284), 24, int(150 * a))
    ImageDraw.Draw(im).text((100, 244), txt, font=f, fill=M.mix((20, 20, 20), (235, 235, 240), a))
