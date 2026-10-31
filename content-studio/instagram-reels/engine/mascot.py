"""Mopshy mascot: a pug in an orange hoodie with a front-desk headset. Pre-rendered parts, composed per frame."""
import math
from PIL import Image, ImageDraw

S = 2  # supersample
CW, CH = 440, 470  # final sprite size

FAWN, FAWN_D = (232, 190, 146), (205, 160, 118)
MASK, EAR = (74, 56, 50), (58, 44, 40)
HOOD, HOOD_D = (255, 101, 49), (214, 78, 34)
NAVY, STEEL = (28, 34, 52), (120, 128, 146)
WHITE, PUPIL = (250, 250, 252), (24, 20, 22)
MOUTH, TONGUE = (92, 24, 34), (236, 112, 128)


def _canvas():
    return Image.new("RGBA", (CW * S, CH * S), (0, 0, 0, 0))


def _e(d, cx, cy, rx, ry, **kw):
    d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], **kw)


def base_sprite():
    im = _canvas()
    d = ImageDraw.Draw(im)
    # hoodie body
    d.rounded_rectangle([90 * S, 330 * S, 350 * S, 520 * S], radius=110 * S, fill=HOOD)
    d.polygon([(170 * S, 335 * S), (220 * S, 395 * S), (270 * S, 335 * S)], fill=HOOD_D)
    d.line([(205 * S, 375 * S), (200 * S, 430 * S)], fill=WHITE, width=5 * S)
    d.line([(235 * S, 375 * S), (240 * S, 430 * S)], fill=WHITE, width=5 * S)
    # ears (behind head)
    d.polygon([(95 * S, 120 * S), (60 * S, 215 * S), (140 * S, 175 * S)], fill=EAR)
    d.polygon([(345 * S, 120 * S), (380 * S, 215 * S), (300 * S, 175 * S)], fill=EAR)
    # head
    _e(d, 220, 200, 150, 140, fill=FAWN)
    _e(d, 220, 250, 140, 85, fill=FAWN_D)
    _e(d, 220, 205, 150, 128, fill=FAWN)
    # forehead wrinkles
    for i, y in enumerate((112, 128)):
        d.arc([(175 - i * 6) * S, y * S, (265 + i * 6) * S, (y + 30) * S], 200, 340, fill=FAWN_D, width=5 * S)
    # dark muzzle mask
    _e(d, 220, 262, 92, 66, fill=MASK)
    # eye patches
    _e(d, 160, 190, 46, 42, fill=(150, 112, 88))
    _e(d, 280, 190, 46, 42, fill=(150, 112, 88))
    # nose
    d.rounded_rectangle([190 * S, 222 * S, 250 * S, 258 * S], radius=16 * S, fill=PUPIL)
    _e(d, 208, 232, 7, 4, fill=(90, 80, 84))
    # headset: band, cups, mic
    d.arc([62 * S, 40 * S, 378 * S, 330 * S], 195, 345, fill=NAVY, width=18 * S)
    d.rounded_rectangle([52 * S, 165 * S, 96 * S, 245 * S], radius=18 * S, fill=NAVY)
    d.rounded_rectangle([344 * S, 165 * S, 388 * S, 245 * S], radius=18 * S, fill=NAVY)
    d.line([(74 * S, 240 * S), (110 * S, 300 * S), (165 * S, 312 * S)], fill=STEEL, width=8 * S, joint="curve")
    _e(d, 172, 312, 13, 11, fill=NAVY)
    return im


def eyes_sprite(closed):
    im = _canvas()
    d = ImageDraw.Draw(im)
    for cx in (160, 280):
        if closed:
            d.arc([(cx - 30) * S, 170 * S, (cx + 30) * S, 205 * S], 10, 170, fill=PUPIL, width=7 * S)
        else:
            _e(d, cx, 190, 33, 33, fill=WHITE)
            _e(d, cx + 4, 193, 21, 22, fill=PUPIL)
            _e(d, cx + 11, 184, 7, 7, fill=WHITE)
    return im


def mouth_sprite(level):
    """level 0..4"""
    im = _canvas()
    d = ImageDraw.Draw(im)
    if level == 0:
        d.arc([196 * S, 256 * S, 222 * S, 282 * S], 20, 160, fill=PUPIL, width=5 * S)
        d.arc([218 * S, 256 * S, 244 * S, 282 * S], 20, 160, fill=PUPIL, width=5 * S)
        return im
    h = 8 + level * 7
    w = 30 + level * 4
    _e(d, 220, 272 + h / 2, w, h, fill=MOUTH)
    _e(d, 220, 272 + h * 0.85, w * 0.6, h * 0.45, fill=TONGUE)
    return im


def _down(im):
    return im.resize((CW, CH), Image.LANCZOS)


class Mascot:
    def __init__(self, scale=1.0):
        self.scale = scale
        base = base_sprite()
        self.frames = {}
        for closed in (False, True):
            for lvl in range(5):
                im = base.copy()
                im.alpha_composite(eyes_sprite(closed))
                im.alpha_composite(mouth_sprite(lvl))
                im = _down(im)
                if scale != 1.0:
                    im = im.resize((int(CW * scale), int(CH * scale)), Image.LANCZOS)
                self.frames[(closed, lvl)] = im

    def draw(self, frame, x, y, t, level, pop=0.0):
        blink = (t % 3.1) < 0.12
        spr = self.frames[(blink, level)]
        tilt = 3.0 * math.sin(t * 1.7) + (4.0 * math.sin(pop * math.pi) if 0 < pop < 1 else 0)
        bob = int(6 * math.sin(t * 2 * math.pi * 0.9))
        squash = 1.0 + (0.06 * math.sin(pop * math.pi) if 0 < pop < 1 else 0)
        if abs(tilt) > 0.3:
            spr = spr.rotate(tilt, resample=Image.BICUBIC, expand=True)
        if squash != 1.0:
            spr = spr.resize((int(spr.width * squash), int(spr.height / squash)), Image.BILINEAR)
        frame.alpha_composite(spr, (int(x - spr.width / 2), int(y - spr.height + bob)))
