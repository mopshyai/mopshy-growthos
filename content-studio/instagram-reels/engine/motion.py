"""Animated text reels for @mopshy.ai: kinetic type, karaoke captions, step tracker, timeline, SFX."""
import math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
COND = "/System/Library/Fonts/Avenir Next Condensed.ttc"
NEXT = "/System/Library/Fonts/Avenir Next.ttc"
BG, GLOW, ORANGE = (10, 13, 20), (68, 33, 27), (255, 101, 49)
WHITE, GREY, DIM = (244, 247, 250), (150, 146, 150), (60, 62, 72)
SAFE_X, SAFE_W = 80, 770
WPM = 165

_fonts = {}


def F(path, size, idx):
    k = (path, size, idx)
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(path, size, index=idx)
    return _fonts[k]


def heavy(s): return F(COND, s, 8)
def medium(s): return F(NEXT, s, 5)
def demi(s): return F(NEXT, s, 2)


def ease_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def ease_back(t):
    t = min(max(t, 0.0), 1.0)
    c = 1.9
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------- background ----------
def make_glow(r, color):
    yy, xx = np.mgrid[-r:r, -r:r].astype(np.float32)
    d = np.sqrt(xx ** 2 + yy ** 2) / r
    a = np.clip(1 - d, 0, 1) ** 2.2 * 255
    spr = Image.new("RGBA", (r * 2, r * 2), color + (0,))
    spr.putalpha(Image.fromarray(a.astype(np.uint8), "L"))
    return spr


GLOW_A = make_glow(720, GLOW)
GLOW_B = make_glow(520, (52, 26, 24))
BASE = Image.new("RGBA", (W, H), BG + (255,))


GLOW_A_RGB = Image.new("RGB", GLOW_A.size, GLOW)
GLOW_B_RGB = Image.new("RGB", GLOW_B.size, (52, 26, 24))
BASE_RGB = Image.new("RGB", (W, H), BG)


def background(t):
    im = BASE_RGB.copy()
    ax = int(W * 0.85 + 140 * math.sin(t * 0.35)) - 720
    ay = int(H * 0.12 + 160 * math.cos(t * 0.27)) - 720
    bx = int(W * 0.1 + 120 * math.cos(t * 0.31)) - 520
    by = int(H * 0.92 + 120 * math.sin(t * 0.22)) - 520
    im.paste(GLOW_A_RGB, (ax, ay), GLOW_A.getchannel("A"))
    im.paste(GLOW_B_RGB, (bx, by), GLOW_B.getchannel("A"))
    return im.convert("RGBA")


# ---------- word sprites ----------
def word_sprite(word, font, color):
    l, t, r, b = font.getbbox(word)
    pad = 12
    img = Image.new("RGBA", (r - l + pad * 2, font.size + pad * 2 + 30), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((pad - l, pad), word, font=font, fill=color)
    return img, pad


def parse_head(text):
    """*word* = orange, ~word~ = struck through. Returns [(word, orange, strike)]."""
    out = []
    for raw in text.split():
        orange = "*" in raw
        strike = "~" in raw
        out.append((raw.replace("*", "").replace("~", ""), orange, strike))
    return out


def layout_head(words, maxw, start=150, floor=70, max_lines=3):
    size = start
    while True:
        f = heavy(size)
        space = f.getlength(" ")
        lines, cur, curw = [], [], 0
        for w in words:
            ww = f.getlength(w[0])
            if cur and curw + space + ww > maxw:
                lines.append(cur)
                cur, curw = [], 0
            cur.append(w)
            curw += (space if len(cur) > 1 else 0) + ww
        lines.append(cur)
        widest = max(f.getlength(w[0]) for w in words)
        if (len(lines) <= max_lines and widest <= maxw) or size <= floor:
            return f, lines
        size -= 6


class Scene:
    def __init__(self, head, say, num=None, tracker=None, timeline=None, dur=None, hook=False):
        self.head, self.say, self.num = head, say, num
        self.tracker, self.timeline, self.hook = tracker, timeline, hook
        spoken = len(say.split()) * 60 / WPM
        self.spoken = spoken
        self.dur = dur or max(1.9, spoken + 0.7)
        self.build()

    def build(self):
        words = parse_head(self.head)
        f, lines = layout_head(words, SAFE_W, 160 if self.hook else 138)
        lh = int(f.size * 1.0)
        num_h = 0
        self.num_sprite = None
        if self.num:
            self.num_sprite, _ = word_sprite(self.num, heavy(170), ORANGE)
            num_h = 175
        block_h = num_h + lh * len(lines)
        center = 640 if self.timeline is not None else 800
        if self.tracker is not None:
            center = max(center, 820)
        top = int(center - block_h / 2)
        self.num_pos = (SAFE_X - 12, top - 12)
        y = top + num_h
        self.items = []
        space = f.getlength(" ")
        k = 0
        for line in lines:
            x = SAFE_X
            for (w, orange, strike) in line:
                spr, pad = word_sprite(w, f, ORANGE if orange else WHITE)
                self.items.append(dict(spr=spr, x=x - pad, y=y - pad, k=k, strike=strike,
                                       w=f.getlength(w), base_y=y, fsize=f.size))
                x += f.getlength(w) + space
                k += 1
            y += lh
        self.head_bottom = y
        self.say_words = self.say.split()

    # caption: karaoke, 2 lines max, sits low in the safe zone
    def draw_caption(self, im, t):
        d = ImageDraw.Draw(im)
        f = medium(46)
        lines, cur = [], []
        for w in self.say_words:
            test = " ".join(cur + [w])
            if cur and f.getlength(test) > SAFE_W:
                lines.append(cur)
                cur = []
            cur.append(w)
        lines.append(cur)
        y = 1300 - (len(lines) - 1) * 60
        if self.timeline is not None:
            y = min(y, 1330)
        per = self.spoken / max(1, len(self.say_words))
        i = 0
        a_in = ease_out(t / 0.25)
        for line in lines:
            x = SAFE_X
            for w in line:
                said = t >= 0.15 + i * per
                col = WHITE if said else GREY
                col = mix(BG, col, a_in)
                d.text((x, y), w, font=f, fill=col)
                x += f.getlength(w + " ")
                i += 1
            y += 60


def draw_tracker(im, spec, t, prev_spec):
    """spec = (labels, states) states: 0 dim, 1 active, 2 done. Animates state changes."""
    labels, states = spec
    pstates = prev_spec[1] if prev_spec and prev_spec[0] == labels else [0] * len(labels)
    d = ImageDraw.Draw(im)
    n = len(labels)
    gap = 14
    total_w = 920
    tw = (total_w - gap * (n - 1)) / n
    y0, hgt = 250, 96
    a = ease_out(t / 0.35)
    f = demi(30 if n > 3 else 34)
    for i, lab in enumerate(labels):
        x0 = 80 + i * (tw + gap)
        s, ps = states[i], pstates[i]
        def look(st):
            if st == 1:
                return ORANGE, ORANGE, BG
            if st == 2:
                return BG, ORANGE, ORANGE
            return BG, DIM, GREY
        fill0, line0, txt0 = look(ps)
        fill1, line1, txt1 = look(s)
        fill, line, txt = mix(fill0, fill1, a), mix(line0, line1, a), mix(txt0, txt1, a)
        grow = 0
        if s == 1 and ps != 1:
            grow = int(10 * math.sin(min(t / 0.35, 1) * math.pi))
        box = [x0 - grow, y0 - grow, x0 + tw + grow, y0 + hgt + grow]
        d.rounded_rectangle(box, radius=18, fill=fill, outline=line, width=4)
        tag = f"{i + 1:02d}"
        d.text((x0 + 18, y0 + 10), tag, font=demi(24), fill=txt)
        lab_w = f.getlength(lab)
        d.text((x0 + (tw - lab_w) / 2 if lab_w < tw - 20 else x0 + 12, y0 + 44), lab, font=f, fill=txt)


def draw_timeline(im, spec, t, prev_upto):
    labels, upto = spec
    d = ImageDraw.Draw(im)
    y = 1080
    x0, x1 = 130, 950
    n = len(labels)
    xs = [x0 + (x1 - x0) * i / (n - 1) for i in range(n)]
    start = prev_upto if prev_upto is not None else -1
    p = start + (upto - start) * ease_out(t / 0.6)
    d.line([(x0, y), (x1, y)], fill=DIM, width=8)
    if p > 0:
        seg = min(p, n - 1)
        xe = x0 + (x1 - x0) * seg / (n - 1)
        d.line([(x0, y), (xe, y)], fill=ORANGE, width=8)
    for i, x in enumerate(xs):
        on = p >= i - 0.02
        r = 22 if on else 16
        if on and i == upto:
            r = 22 + int(6 * (0.5 + 0.5 * math.sin(t * 6)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=ORANGE if on else BG, outline=ORANGE if on else DIM, width=5)
        lab = labels[i]
        f = demi(34)
        d.text((x - f.getlength(lab) / 2, y + 42), lab, font=f, fill=WHITE if on else GREY)


def render_frame(scene, t, prev, gt):
    im = background(gt)
    if scene.tracker:
        draw_tracker(im, scene.tracker, t, prev.tracker if prev else None)
    if scene.timeline:
        draw_timeline(im, scene.timeline, t, prev.timeline[1] if prev and prev.timeline else None)
    # exit: last 0.18s
    out_t = max(0.0, (t - (scene.dur - 0.18)) / 0.18)
    exit_a = 1 - ease_out(out_t)
    exit_dy = -int(50 * ease_out(out_t))
    stagger = 0.07 if not scene.hook else 0.11
    base = 0.0
    if scene.num_sprite is not None:
        tt = (t - 0.0) / 0.3
        a = ease_out(tt) * exit_a
        dx = int(-90 * (1 - ease_out(tt)))
        put(im, scene.num_sprite, scene.num_pos[0] + dx, scene.num_pos[1] + exit_dy, a)
        base = 0.12
    for it in scene.items:
        st = base + it["k"] * stagger
        tt = (t - st) / 0.32
        if tt <= 0:
            continue
        a = ease_out(tt) * exit_a
        if scene.hook:
            sc = 1.35 - 0.35 * ease_back(tt)
            spr = it["spr"]
            if abs(sc - 1) > 0.01:
                spr = spr.resize((max(1, int(spr.width * sc)), max(1, int(spr.height * sc))), Image.BILINEAR)
            cx = it["x"] + it["spr"].width / 2
            cy = it["y"] + it["spr"].height / 2
            put(im, spr, int(cx - spr.width / 2), int(cy - spr.height / 2) + exit_dy, a)
        else:
            dy = int(70 * (1 - ease_out(tt)))
            put(im, it["spr"], it["x"], it["y"] + dy + exit_dy, a)
        if it["strike"]:
            s0 = base + len(scene.items) * stagger + 0.25
            p = ease_out((t - s0) / 0.3)
            if p > 0:
                d = ImageDraw.Draw(im)
                yy = it["base_y"] + int(it["fsize"] * 0.52) + exit_dy
                d.rectangle([it["x"] + 12, yy, it["x"] + 12 + int(it["w"] * p), yy + 14],
                            fill=ORANGE + (int(255 * exit_a),))
    scene.draw_caption(im, t)
    return im.convert("RGB")


def put(im, spr, x, y, a):
    x, y = int(x), int(y)
    if a <= 0.01:
        return
    if a < 0.99:
        spr = spr.copy()
        alpha = spr.getchannel("A").point(lambda v: int(v * a))
        spr.putalpha(alpha)
    im.alpha_composite(spr, (max(0, x), max(0, y))) if x >= 0 and y >= 0 else im.paste(spr, (x, y), spr)


# ---------- audio ----------
def sfx_track(starts, ticks, total, path, sr=44100):
    n = int(total * sr) + sr
    buf = np.zeros(n, dtype=np.float32)
    rng = np.random.default_rng(7)
    L = int(0.32 * sr)
    noise = rng.standard_normal(L).astype(np.float32)
    # crude band-pass sweep: moving average lowpass minus a heavier one
    k1 = np.ones(6) / 6
    k2 = np.ones(60) / 60
    swoosh = np.convolve(noise, k1, "same") - np.convolve(noise, k2, "same")
    env = np.sin(np.linspace(0, math.pi, L)) ** 2
    swoosh = swoosh * env * 0.16
    tl = int(0.09 * sr)
    tt = np.arange(tl) / sr
    tick = (np.sin(2 * math.pi * 1650 * tt) * np.exp(-tt * 55) * 0.18).astype(np.float32)
    for s in starts:
        i = int(max(0, s - 0.08) * sr)
        buf[i:i + L] += swoosh[: len(buf[i:i + L])]
    for s in ticks:
        i = int(s * sr)
        buf[i:i + tl] += tick[: len(buf[i:i + tl])]
    buf = np.clip(buf, -1, 1)
    pcm = (buf * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def render(scenes, out_mp4, cover_path, wav_path):
    total = sum(s.dur for s in scenes)
    starts, ticks = [], []
    g = 0.0
    prev = None
    for s in scenes:
        starts.append(g)
        if s.tracker and (not prev or prev.tracker != s.tracker):
            ticks.append(g + 0.05)
        if s.timeline and (not prev or prev.timeline != s.timeline):
            ticks.append(g + 0.4)
        g += s.dur
    sfx_track(starts, ticks, total, wav_path)
    proc = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav_path,
        "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", out_mp4],
        stdin=subprocess.PIPE)
    g = 0.0
    prev = None
    cover_done = False
    for s in scenes:
        nf = int(round(s.dur * FPS))
        for i in range(nf):
            t = i / FPS
            fr = render_frame(s, t, prev, g + t)
            if not cover_done and t >= min(s.dur - 0.3, 1.4):
                fr.save(cover_path, quality=92)
                cover_done = True
            proc.stdin.write(fr.tobytes())
        g += nf / FPS
        prev = s
    proc.stdin.close()
    proc.wait()
    return total
