"""Human-edit layer: real b-roll, site screen recordings, handheld shake, punch-ins, grain, PiP mascot."""
import math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import motion as M
import motion2 as V
from motion import W, H, FPS, SAFE_X, SAFE_W, ORANGE, WHITE, GREY, BG, heavy, medium, demi, ease_out, ease_back, put
from mascot import Mascot

PIP = Mascot(0.52)
rng = np.random.default_rng(3)
GRAIN = []
for _ in range(6):
    g = rng.normal(128, 38, (H // 2, W // 2)).clip(0, 255).astype(np.uint8)
    gi = Image.fromarray(g, "L").resize((W, H), Image.NEAREST)
    GRAIN.append(gi)


def grain(im, i):
    return Image.blend(im, Image.merge("RGB", [GRAIN[i % 6]] * 3), 0.045)


def shade_overlay():
    a = np.zeros((H, W), np.float32)
    ys = np.arange(H, dtype=np.float32)[:, None]
    a += np.clip(1 - ys / 900, 0, 1) ** 1.4 * 200          # top
    a += np.clip((ys - 1050) / 870, 0, 1) ** 1.2 * 235     # bottom
    ov = Image.new("RGBA", (W, H), (6, 8, 12, 0))
    ov.putalpha(Image.fromarray(a.clip(0, 235).astype(np.uint8), "L"))
    return ov


SHADE = shade_overlay()


class Clip:
    """Streams a b-roll clip as 1080x1920 frames with a little headroom for shake and zoom."""
    PAD = 1.12

    def __init__(self, path, start, nframes):
        self.w, self.h = int(W * self.PAD) // 2 * 2, int(H * self.PAD) // 2 * 2
        self.p = subprocess.Popen([
            "ffmpeg", "-loglevel", "error", "-stream_loop", "-1", "-ss", str(start), "-i", path,
            "-vf", f"fps={FPS},scale={self.w}:{self.h}:force_original_aspect_ratio=increase,crop={self.w}:{self.h},eq=saturation=0.92:contrast=1.04",
            "-frames:v", str(nframes + 2), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.last = None

    def next(self):
        buf = self.p.stdout.read(self.w * self.h * 3)
        if len(buf) == self.w * self.h * 3:
            self.last = Image.frombuffer("RGB", (self.w, self.h), buf)
        return self.last

    def close(self):
        self.p.stdout.close()
        self.p.wait()


class BrollScene(V.VScene):
    def __init__(self, head, say, vo, clip, start=0.0, **kw):
        self.clip_path, self.clip_start = clip, start
        super().__init__(head, say, vo, **kw)

    def build(self):
        words = M.parse_head(self.head)
        f, lines = M.layout_head(words, SAFE_W + 60, 128 if self.hook else 112, 64, 3)
        lh = int(f.size * 1.0)
        top = 300
        self.num_sprite = None
        self.items = []
        space = f.getlength(" ")
        y, k = top, 0
        for line in lines:
            x = SAFE_X
            for (w, orange, strike) in line:
                spr, padd = M.word_sprite(w, f, ORANGE if orange else WHITE)
                self.items.append(dict(spr=spr, x=x - padd, y=y - padd, k=k, strike=strike,
                                       w=f.getlength(w), base_y=y, fsize=f.size))
                x += f.getlength(w) + space
                k += 1
            y += lh
        disp = self.say
        for k, v in V.DISPLAY.items():
            disp = disp.replace(k, v)
        self.say_words = disp.split()


class ScreenScene(V.VScene):
    """A page from mopshy.com in a browser frame, panning between two crop boxes, with a moving cursor."""
    def __init__(self, head, say, vo, image, url, box_a, box_b, cursor=None, **kw):
        self.page = Image.open(image).convert("RGB")
        self.url, self.box_a, self.box_b, self.cursor = url, box_a, box_b, cursor
        super().__init__(head, say, vo, **kw)

    def build(self):
        super().build()
        # headline sits above the browser window
        f, lines = M.layout_head(M.parse_head(self.head), SAFE_W, 96, 60, 2)
        self.items = []
        space = f.getlength(" ")
        y, k = 290, 0
        for line in lines:
            x = SAFE_X
            for (w, orange, strike) in line:
                spr, padd = M.word_sprite(w, f, ORANGE if orange else WHITE)
                self.items.append(dict(spr=spr, x=x - padd, y=y - padd, k=k, strike=strike,
                                       w=f.getlength(w), base_y=y, fsize=f.size))
                x += f.getlength(w) + space
                k += 1
            y += int(f.size)
        self.win_top = y + 30
        self.num_sprite = None


def lerp_box(a, b, p):
    return tuple(a[i] + (b[i] - a[i]) * p for i in range(4))


def draw_browser(im, scene, t):
    x0, x1 = 60, 1020
    y0 = scene.win_top
    y1 = 1200
    d = ImageDraw.Draw(im)
    pop = ease_back(t / 0.45)
    if pop < 0.02:
        return
    # window shadow + chrome
    sh = Image.new("RGBA", (x1 - x0 + 60, y1 - y0 + 60), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([30, 30, x1 - x0 + 30, y1 - y0 + 30], radius=26, fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    off = int((1 - pop) * 120)
    im.alpha_composite(sh, (x0 - 30, y0 - 22 + off))
    d.rounded_rectangle([x0, y0 + off, x1, y1 + off], radius=24, fill=(30, 33, 42))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([x0 + 26 + i * 30, y0 + 22 + off, x0 + 44 + i * 30, y0 + 40 + off], fill=c)
    d.rounded_rectangle([x0 + 130, y0 + 14 + off, x1 - 30, y0 + 50 + off], radius=16, fill=(18, 20, 26))
    d.text((x0 + 152, y0 + 20 + off), scene.url, font=medium(24), fill=(200, 200, 208))
    # page content: pan from box_a to box_b
    p = ease_out(max(0, (t - 0.5)) / max(0.6, scene.dur - 1.0))
    vw, vh = x1 - x0 - 16, y1 - y0 - 72
    asp = vw / vh
    ba = (scene.box_a[0], scene.box_a[1], scene.box_a[0] + scene.box_a[2], scene.box_a[1] + scene.box_a[2] / asp)
    bb = (scene.box_b[0], scene.box_b[1], scene.box_b[0] + scene.box_b[2], scene.box_b[1] + scene.box_b[2] / asp)
    bx = lerp_box(ba, bb, p)
    crop = scene.page.crop(tuple(int(v) for v in bx)).resize((vw, vh), Image.BICUBIC)
    mask = Image.new("L", (vw, vh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, vw, vh], radius=16, fill=255)
    im.paste(crop, (x0 + 8, y0 + 64 + off), mask)
    # cursor glides to a target, then clicks
    if scene.cursor:
        (cx0, cy0), (cx1, cy1) = scene.cursor
        q = ease_out(max(0, t - 0.6) / 1.2)
        cx, cy = cx0 + (cx1 - cx0) * q, cy0 + (cy1 - cy0) * q + off
        if q >= 0.999 and (t % 1.6) < 0.25:
            d.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], outline=ORANGE, width=4)
        pts = [(cx, cy), (cx, cy + 46), (cx + 12, cy + 35), (cx + 22, cy + 56), (cx + 30, cy + 52), (cx + 20, cy + 32), (cx + 36, cy + 32)]
        d.polygon(pts, fill=(255, 255, 255), outline=(0, 0, 0))


def render_frame(scene, t, prev, gt, fidx, clip_frame=None):
    if isinstance(scene, BrollScene) and clip_frame is not None:
        # handheld drift + slow push-in
        z = 1.0 + 0.06 * (t / scene.dur)
        sx = 14 * math.sin(gt * 1.3) + 5 * math.sin(gt * 3.7)
        sy = 12 * math.cos(gt * 1.1) + 4 * math.sin(gt * 4.1)
        cw, ch = clip_frame.size
        vw, vh = W / z * 1.0, H / z * 1.0
        left = (cw - vw) / 2 + sx
        top = (ch - vh) / 2 + sy
        im = clip_frame.crop((int(left), int(top), int(left + vw), int(top + vh))).resize((W, H), Image.BILINEAR).convert("RGBA")
        im.alpha_composite(SHADE)
    else:
        im = M.background(gt)
    if scene.tracker:
        M.draw_tracker(im, scene.tracker, t, prev.tracker if prev else None)
    if scene.timeline:
        M.draw_timeline_at(im, scene.timeline, t, prev.timeline[1] if prev and prev.timeline else None, 770)
    if isinstance(scene, ScreenScene):
        draw_browser(im, scene, t)
    lvl = scene.levels[min(len(scene.levels) - 1, int(t * FPS))]
    if isinstance(scene, (BrollScene, ScreenScene)):
        # picture-in-picture narrator, bottom right of the safe zone
        d = ImageDraw.Draw(im)
        cx, cy = 720, 1150
        d.ellipse([cx - 128, cy - 128, cx + 128, cy + 128], fill=(20, 24, 34), outline=ORANGE, width=6)
        holder = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        PIP.draw(holder, 128, 300, gt, lvl)
        m = Image.new("L", (256, 256), 0)
        ImageDraw.Draw(m).ellipse([6, 6, 250, 250], fill=255)
        im.paste(holder, (cx - 128, cy - 128), Image.composite(holder.getchannel("A"), Image.new("L", (256, 256), 0), m))
    else:
        V.MASCOT.draw(im, 690, 1262, gt, lvl, pop=t / 0.35)
    out_t = max(0.0, (t - (scene.dur - 0.12)) / 0.12)
    exit_a = 1 - ease_out(out_t)
    stagger = 0.11 if scene.hook else 0.07
    base = 0.0
    if scene.num_sprite is not None:
        tt = t / 0.3
        put(im, scene.num_sprite, scene.num_pos[0] + int(-90 * (1 - ease_out(tt))), scene.num_pos[1], ease_out(tt) * exit_a)
        base = 0.12
    for it in scene.items:
        tt = (t - base - it["k"] * stagger) / 0.3
        if tt <= 0:
            continue
        a = ease_out(tt) * exit_a
        if scene.hook:
            sc = 1.35 - 0.35 * ease_back(tt)
            spr = it["spr"]
            if abs(sc - 1) > 0.01:
                spr = spr.resize((max(1, int(spr.width * sc)), max(1, int(spr.height * sc))), Image.BILINEAR)
            cx, cy = it["x"] + it["spr"].width / 2, it["y"] + it["spr"].height / 2
            put(im, spr, int(cx - spr.width / 2), int(cy - spr.height / 2), a)
        else:
            put(im, it["spr"], it["x"], it["y"] + int(60 * (1 - ease_out(tt))), a)
        if it["strike"]:
            p = ease_out((t - (base + len(scene.items) * stagger + 0.25)) / 0.3)
            if p > 0:
                yy = it["base_y"] + int(it["fsize"] * 0.52)
                ImageDraw.Draw(im).rectangle([it["x"] + 12, yy, it["x"] + 12 + int(it["w"] * p), yy + 12], fill=ORANGE + (int(255 * exit_a),))
    scene.draw_caption(im, t)
    out = im.convert("RGB")
    # jump-cut punch-in on every other text scene, like a hand edit
    if getattr(scene, "punch", False):
        z = 1.07
        cw, ch = int(W / z), int(H / z)
        l, tp = (W - cw) // 2, (H - ch) // 2 - 40
        out = out.crop((l, tp, l + cw, tp + ch)).resize((W, H), Image.BILINEAR)
    if t < 0.07 and prev is not None:
        out = Image.blend(out, Image.new("RGB", (W, H), (255, 255, 255)), 0.18)  # cut flash
    return grain(out, fidx)


def room_tone(n, sr=44100):
    x = np.cumsum(rng.normal(0, 1, n)).astype(np.float32)
    x -= np.convolve(x, np.ones(2000) / 2000, "same")
    x /= (np.abs(x).max() + 1e-6)
    return x * 0.012


def render(scenes, out_mp4, cover_path, wav_path):
    SR = V.SR
    total_frames = sum(int(round(s.dur * FPS)) for s in scenes)
    total = total_frames / FPS
    n = int(total * SR) + SR
    mixbuf = room_tone(n)
    starts, ticks = [], []
    g = 0.0
    prev = None
    for s in scenes:
        starts.append(g)
        if s.tracker and (not prev or prev.tracker != s.tracker):
            ticks.append(g + 0.05)
        if s.timeline and (not prev or prev.timeline != s.timeline):
            ticks.append(g + 0.4)
        i = int((g + s.lead) * SR)
        seg = s.vo_audio[: max(0, min(len(s.vo_audio), n - i))]
        mixbuf[i:i + len(seg)] += seg * 0.95
        g += int(round(s.dur * FPS)) / FPS
        prev = s
    M.sfx_track(starts, ticks, total, wav_path + ".sfx.wav")
    with wave.open(wav_path + ".sfx.wav") as w:
        sfx = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    m = min(len(sfx), n)
    mixbuf[:m] += sfx[:m] * 0.4
    mixbuf = np.clip(mixbuf, -1, 1)
    with wave.open(wav_path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mixbuf * 32767).astype(np.int16).tobytes())
    proc = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav_path,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
        "-shortest", "-movflags", "+faststart", out_mp4], stdin=subprocess.PIPE)
    g = 0.0
    prev = None
    fidx = 0
    cover_done = False
    text_count = 0
    for s in scenes:
        nf = int(round(s.dur * FPS))
        clip = Clip(s.clip_path, s.clip_start, nf) if isinstance(s, BrollScene) else None
        if not isinstance(s, (BrollScene, ScreenScene)):
            text_count += 1
            s.punch = text_count % 2 == 0
        for i in range(nf):
            t = i / FPS
            fr = render_frame(s, t, prev, g + t, fidx, clip.next() if clip else None)
            if not cover_done and t >= min(s.dur - 0.3, 1.5):
                fr.save(cover_path, quality=92)
                cover_done = True
            proc.stdin.write(fr.tobytes())
            fidx += 1
        if clip:
            clip.close()
        g += nf / FPS
        prev = s
    proc.stdin.close()
    proc.wait()
    return total
