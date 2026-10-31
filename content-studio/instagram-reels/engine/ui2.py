"""Redesigned on-video UI: frosted-glass step cards and a bolder timeline."""
import math
from PIL import Image, ImageDraw, ImageFilter
import motion as M
from motion import ORANGE, WHITE, BG, heavy, demi, ease_out, ease_back

NAVY = (14, 18, 30)


def _glass(im, box, radius, tint, blur=16):
    x0, y0, x1, y1 = [int(v) for v in box]
    region = im.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(blur))
    over = Image.new("RGBA", region.size, tint)
    region = Image.alpha_composite(region.convert("RGBA"), over)
    mask = Image.new("L", region.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, region.width - 1, region.height - 1], radius=radius, fill=255)
    im.paste(region, (x0, y0), mask)


def _glow(im, box, radius, color, strength):
    x0, y0, x1, y1 = [int(v) for v in box]
    pad = 40
    g = Image.new("RGBA", (x1 - x0 + pad * 2, y1 - y0 + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(g).rounded_rectangle([pad, pad, pad + x1 - x0, pad + y1 - y0], radius=radius, fill=color + (int(170 * strength),))
    g = g.filter(ImageFilter.GaussianBlur(22))
    im.alpha_composite(g, (x0 - pad, y0 - pad))


def _check(d, cx, cy, r, color):
    d.line([(cx - r * 0.45, cy + r * 0.02), (cx - r * 0.1, cy + r * 0.38), (cx + r * 0.5, cy - r * 0.35)],
           fill=color, width=max(4, int(r * 0.28)), joint="curve")


def draw_tracker(im, spec, t, prev_spec):
    labels, states = spec
    pstates = prev_spec[1] if prev_spec and prev_spec[0] == labels else [0] * len(labels)
    n = len(labels)
    gap, x_start, total_w = 16, 66, 948
    tw = (total_w - gap * (n - 1)) / n
    y0, hgt = 236, 128
    a = ease_out(t / 0.35)
    lab_font = heavy(46 if n <= 3 else 40)
    avail0 = tw - (44 + 44) - 14
    longest = max((w for l in labels for w in ([l] if len(l.split()) == 1 else l.split())), key=lambda w: lab_font.getlength(w))
    while lab_font.getlength(longest) > avail0 and lab_font.size > 30:
        lab_font = heavy(lab_font.size - 2)
    num_font = heavy(30)
    for i, lab in enumerate(labels):
        s, ps = states[i], pstates[i]
        x0 = x_start + i * (tw + gap)
        # active card springs up when it turns on
        sc = 1.0
        if s == 1:
            sc = 1.0 + 0.06 * (ease_back(t / 0.4) if ps != 1 else 1.0)
        cw, ch = tw * sc, hgt * sc
        cx0, cy0 = x0 + (tw - cw) / 2, y0 + (hgt - ch) / 2
        box = (cx0, cy0, cx0 + cw, cy0 + ch)
        on = a if (s == 1 and ps != 1) else (1.0 if s == 1 else 0.0)
        if s == 1:
            _glow(im, box, 30, ORANGE, on)
        _glass(im, box, 30, (10, 12, 20, 120))
        d = ImageDraw.Draw(im)
        if s == 1:
            d.rounded_rectangle(box, radius=30, fill=M.mix(NAVY, ORANGE, on))
        elif s == 2:
            d.rounded_rectangle(box, radius=30, outline=ORANGE, width=4)
        else:
            d.rounded_rectangle(box, radius=30, outline=(120, 124, 138), width=3)
        # badge: number, or a check when done
        r = 22 * sc
        bx, by = box[0] + 20 + r, box[1] + ch / 2
        if s == 2:
            d.ellipse([bx - r, by - r, bx + r, by + r], fill=ORANGE)
            _check(d, bx, by, r, NAVY)
        elif s == 1:
            d.ellipse([bx - r, by - r, bx + r, by + r], fill=M.mix(ORANGE, NAVY, on))
            num = f"{i + 1}"
            d.text((bx - num_font.getlength(num) / 2, by - num_font.size * 0.62), num, font=num_font, fill=M.mix(NAVY, ORANGE, on))
        else:
            d.ellipse([bx - r, by - r, bx + r, by + r], outline=(200, 200, 210), width=3)
            num = f"{i + 1}"
            d.text((bx - num_font.getlength(num) / 2, by - num_font.size * 0.62), num, font=num_font, fill=(200, 200, 210))
        # label, auto-shrunk to fit beside the badge, two lines if needed
        avail = cw - (2 * r + 44) - 14
        f = lab_font
        words = lab.split()
        lines = [lab]
        if f.getlength(lab) > avail and len(words) > 1:
            lines = [words[0], " ".join(words[1:])]
        col = NAVY if s == 1 else (WHITE if s == 2 else (225, 225, 232))
        if s == 1:
            col = M.mix(WHITE, NAVY, on)
        lh = f.size * 0.98
        ty = by - lh * len(lines) / 2 - f.size * 0.1
        for li, line in enumerate(lines):
            d.text((bx + r + 16, ty + li * lh), line, font=f, fill=col)


def draw_timeline_at(im, spec, t, prev_upto, y):
    labels, upto = spec
    x0, x1 = 150, 810
    _glass(im, (70, y - 120, 890, y + 70), 30, (10, 12, 20, 130))
    d = ImageDraw.Draw(im)
    n = len(labels)
    start = prev_upto if prev_upto is not None else -1
    p = start + (upto - start) * ease_out(t / 0.6)
    d.rounded_rectangle([x0, y - 6, x1, y + 6], radius=6, fill=(88, 92, 106))
    if p > 0:
        d.rounded_rectangle([x0, y - 6, x0 + (x1 - x0) * min(p, n - 1) / (n - 1), y + 6], radius=6, fill=ORANGE)
    f = heavy(38)
    for i in range(n):
        x = x0 + (x1 - x0) * i / (n - 1)
        on = p >= i - 0.02
        r = 20
        if on and i == upto:
            r = 22 + 4 * (0.5 + 0.5 * math.sin(t * 6))
        if on:
            d.ellipse([x - r, y - r, x + r, y + r], fill=ORANGE)
            _check(d, x, y, r, NAVY)
        else:
            d.ellipse([x - r, y - r, x + r, y + r], fill=NAVY, outline=(200, 200, 210), width=4)
        lab = labels[i]
        d.text((x - f.getlength(lab) / 2, y - 88), lab, font=f, fill=WHITE if on else (190, 190, 200))


M.draw_tracker = draw_tracker
M.draw_timeline_at = draw_timeline_at
