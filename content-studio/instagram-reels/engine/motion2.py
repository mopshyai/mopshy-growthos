"""Voice + mascot layer on top of motion.py."""
import json, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw
import motion as M
from motion import W, H, FPS, SAFE_X, SAFE_W, ORANGE, WHITE, GREY, BG, heavy, medium, ease_out, ease_back, mix, put, word_sprite, parse_head, layout_head
from mascot import Mascot

SR = 44100
MASCOT = Mascot(0.86)


def load_wav(mp3):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", mp3, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768


def a_in0(t):
    return ease_out(t / 0.2)


DISPLAY = {"12 dollar": "$12", "9 dollar": "$9", "10 dollar": "$10"}


class VScene(M.Scene):
    def __init__(self, head, say, vo, num=None, tracker=None, timeline=None, hook=False, pad=0.35):
        self.vo_audio = load_wav(vo + ".mp3")
        self.words = json.load(open(vo + ".json"))
        self.lead = 0.08
        vo_dur = len(self.vo_audio) / SR
        super().__init__(head, say, num=num, tracker=tracker, timeline=timeline, hook=hook,
                         dur=self.lead + vo_dur + pad)
        # mouth level per frame from RMS
        hop = SR // FPS
        n = int(math.ceil(self.dur * FPS)) + 2
        lv = []
        peak = max(1e-4, float(np.percentile(np.abs(self.vo_audio), 99)))
        for i in range(n):
            s = int((i / FPS - self.lead) * SR)
            seg = self.vo_audio[max(0, s): max(0, s) + hop]
            r = float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 0.0
            lv.append(min(4, int(r / (peak * 0.42) * 4 + 0.35)) if r > peak * 0.03 else 0)
        self.levels = lv

    def build(self):
        words = parse_head(self.head)
        tl = self.timeline is not None
        f, lines = layout_head(words, SAFE_W, 132 if self.hook else 116, 64, 3)
        lh = int(f.size * 1.0)
        num_h = 0
        self.num_sprite = None
        if self.num:
            self.num_sprite, _ = word_sprite(self.num, heavy(120), ORANGE)
            num_h = 125
        block_h = num_h + lh * len(lines)
        lo, hi = (390, 690) if tl else (390, 830)
        top = int(max(lo, (lo + hi) / 2 - block_h / 2))
        self.num_pos = (SAFE_X - 12, top - 12)
        y = top + num_h
        self.items = []
        space = f.getlength(" ")
        k = 0
        for line in lines:
            x = SAFE_X
            for (w, orange, strike) in line:
                spr, padd = word_sprite(w, f, ORANGE if orange else WHITE)
                self.items.append(dict(spr=spr, x=x - padd, y=y - padd, k=k, strike=strike,
                                       w=f.getlength(w), base_y=y, fsize=f.size))
                x += f.getlength(w) + space
                k += 1
            y += lh
        disp = self.say
        for k, v in DISPLAY.items():
            disp = disp.replace(k, v)
        self.say_words = disp.split()

    def draw_caption(self, im, t):
        d = ImageDraw.Draw(im)
        f = medium(44)
        lines, cur = [], []
        for w in self.say_words:
            if cur and f.getlength(" ".join(cur + [w])) > SAFE_W:
                lines.append(cur)
                cur = []
            cur.append(w)
        lines.append(cur)
        y = 1300
        widest = max(f.getlength(" ".join(l)) for l in lines)
        box = Image.new("RGBA", (int(widest) + 44, len(lines) * 58 + 26), (0, 0, 0, 0))
        ImageDraw.Draw(box).rounded_rectangle([0, 0, box.width - 1, box.height - 1], radius=18, fill=(8, 10, 16, int(175 * a_in0(t))))
        im.alpha_composite(box, (SAFE_X - 22, y - 10))
        nb, nc = len(self.words), len(self.say_words)
        a_in = ease_out(t / 0.2)
        i = 0
        for line in lines:
            x = SAFE_X
            for w in line:
                j = min(nb - 1, int(i * nb / max(1, nc))) if nb else 0
                start = (self.words[j][0] if nb else i * 0.3) + self.lead
                col = WHITE if t >= start else GREY
                d.text((x, y), w, font=f, fill=mix(BG, col, a_in))
                x += f.getlength(w + " ")
                i += 1
            y += 58


def render_frame(scene, t, prev, gt):
    im = M.background(gt)
    if scene.tracker:
        M.draw_tracker(im, scene.tracker, t, prev.tracker if prev else None)
    if scene.timeline:
        M.draw_timeline_at(im, scene.timeline, t, prev.timeline[1] if prev and prev.timeline else None, 770)
    lvl = scene.levels[min(len(scene.levels) - 1, int(t * FPS))]
    MASCOT.draw(im, 690, 1262, gt, lvl, pop=t / 0.35)
    out_t = max(0.0, (t - (scene.dur - 0.16)) / 0.16)
    exit_a = 1 - ease_out(out_t)
    exit_dy = -int(50 * ease_out(out_t))
    stagger = 0.11 if scene.hook else 0.07
    base = 0.0
    if scene.num_sprite is not None:
        tt = t / 0.3
        put(im, scene.num_sprite, scene.num_pos[0] + int(-90 * (1 - ease_out(tt))), scene.num_pos[1] + exit_dy, ease_out(tt) * exit_a)
        base = 0.12
    for it in scene.items:
        tt = (t - base - it["k"] * stagger) / 0.32
        if tt <= 0:
            continue
        a = ease_out(tt) * exit_a
        if scene.hook:
            sc = 1.35 - 0.35 * ease_back(tt)
            spr = it["spr"]
            if abs(sc - 1) > 0.01:
                spr = spr.resize((max(1, int(spr.width * sc)), max(1, int(spr.height * sc))), Image.BILINEAR)
            cx, cy = it["x"] + it["spr"].width / 2, it["y"] + it["spr"].height / 2
            put(im, spr, int(cx - spr.width / 2), int(cy - spr.height / 2) + exit_dy, a)
        else:
            put(im, it["spr"], it["x"], it["y"] + int(70 * (1 - ease_out(tt))) + exit_dy, a)
        if it["strike"]:
            p = ease_out((t - (base + len(scene.items) * stagger + 0.25)) / 0.3)
            if p > 0:
                yy = it["base_y"] + int(it["fsize"] * 0.52) + exit_dy
                ImageDraw.Draw(im).rectangle([it["x"] + 12, yy, it["x"] + 12 + int(it["w"] * p), yy + 12], fill=ORANGE + (int(255 * exit_a),))
    scene.draw_caption(im, t)
    return im.convert("RGB")


def draw_timeline_at(im, spec, t, prev_upto, y):
    labels, upto = spec
    d = ImageDraw.Draw(im)
    x0, x1 = 130, 830
    n = len(labels)
    start = prev_upto if prev_upto is not None else -1
    p = start + (upto - start) * ease_out(t / 0.6)
    d.line([(x0, y), (x1, y)], fill=M.DIM, width=8)
    if p > 0:
        d.line([(x0, y), (x0 + (x1 - x0) * min(p, n - 1) / (n - 1), y)], fill=ORANGE, width=8)
    for i in range(n):
        x = x0 + (x1 - x0) * i / (n - 1)
        on = p >= i - 0.02
        r = 20 if on else 14
        if on and i == upto:
            r = 20 + int(5 * (0.5 + 0.5 * math.sin(t * 6)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=ORANGE if on else BG, outline=ORANGE if on else M.DIM, width=5)
        fnt = M.demi(32)
        d.text((x - fnt.getlength(labels[i]) / 2, y - 70), labels[i], font=fnt, fill=WHITE if on else GREY)


M.draw_timeline_at = draw_timeline_at


def render(scenes, out_mp4, cover_path, wav_path):
    total_frames = sum(int(round(s.dur * FPS)) for s in scenes)
    total = total_frames / FPS
    n = int(total * SR) + SR
    mixbuf = np.zeros(n, dtype=np.float32)
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
        mixbuf[i:i + len(s.vo_audio)] += s.vo_audio[: len(mixbuf[i:i + len(s.vo_audio)])] * 0.95
        g += int(round(s.dur * FPS)) / FPS
        prev = s
    M.sfx_track(starts, ticks, total, wav_path + ".sfx.wav")
    with wave.open(wav_path + ".sfx.wav") as w:
        sfx = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    mixbuf[: len(sfx)] += sfx[: n] * 0.45
    mixbuf = np.clip(mixbuf, -1, 1)
    with wave.open(wav_path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mixbuf * 32767).astype(np.int16).tobytes())
    proc = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav_path,
        "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
        "-shortest", "-movflags", "+faststart", out_mp4], stdin=subprocess.PIPE)
    g = 0.0
    prev = None
    cover_done = False
    for s in scenes:
        nf = int(round(s.dur * FPS))
        for i in range(nf):
            t = i / FPS
            fr = render_frame(s, t, prev, g + t)
            if not cover_done and t >= min(s.dur - 0.3, 1.6):
                fr.save(cover_path, quality=92)
                cover_done = True
            proc.stdin.write(fr.tobytes())
        g += nf / FPS
        prev = s
    proc.stdin.close()
    proc.wait()
    return total
