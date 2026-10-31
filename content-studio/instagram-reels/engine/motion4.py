"""Fast-cut 'human editor' reels: people b-roll on every line, word-pop captions, zoom punches, music bed."""
import json, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import motion as M
import motion3 as M3
import widgets
import ui2  # noqa: F401  (redesigned tracker/timeline)
from motion import W, H, FPS, ORANGE, WHITE, BG, heavy, medium, ease_out, ease_back

SR = 44100
EMOJI = "/System/Library/Fonts/Apple Color Emoji.ttc"


def load_audio(path, ch=1):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "s16le", "-ac", str(ch), "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768


def emoji_sprite(ch, size=200):
    f = ImageFont.truetype(EMOJI, 160)
    im = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((20, 20), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    return im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)


class Line:
    """One voiced line: its audio, word timings, shots and overlays."""
    def __init__(self, say, vo, shots, hi=(), head=None, tracker=None, timeline=None, emoji=None, screen=None, widget=None):
        self.widget = widget
        self.say, self.shots, self.hi = say, shots, set(w.lower() for w in hi)
        self.head, self.tracker, self.timeline, self.emoji, self.screen = head, tracker, timeline, emoji, screen
        self.audio = load_audio(vo + ".mp3")
        self.words = json.load(open(vo + ".json"))
        self.lead = 0.04
        self.dur = self.lead + len(self.audio) / SR + 0.12
        disp = say
        for k, v in {"12 dollar": "$12", "9 dollar": "$9", "10 dollar": "$10"}.items():
            disp = disp.replace(k, v)
        self.disp = disp.split()
        # caption chunks: up to 3 words, break after punctuation
        chunks, cur = [], []
        for i, w in enumerate(self.disp):
            cur.append(i)
            if len(cur) == 3 or w[-1] in ".,?!:" or (len(cur) == 2 and len(w) > 9):
                chunks.append(cur)
                cur = []
        if cur:
            chunks.append(cur)
        nb, nc = len(self.words), len(self.disp)
        def start(i):
            j = min(nb - 1, int(i * nb / max(1, nc)))
            return self.words[j][0] + self.lead
        self.chunks = [(start(c[0]), [self.disp[i] for i in c]) for c in chunks]
        self.emoji_spr = emoji_sprite(emoji) if emoji else None
        self.head_items = None
        if head:
            words = M.parse_head(head)
            f, lines = M.layout_head(words, 840, 132, 70, 3)
            items, y, k = [], 300, 0
            for line in lines:
                x = 80
                for (w, orange, strike) in line:
                    spr = stroked(w, f, ORANGE if orange else WHITE, 6)
                    items.append((spr, x - 10, y - 10, k, strike, f.getlength(w), f.size))
                    x += f.getlength(w) + f.getlength(" ")
                    k += 1
                y += int(f.size * 1.0)
            self.head_items = items
            self.head_bottom = y


def stroked(text, font, color, sw):
    l, t, r, b = font.getbbox(text, stroke_width=sw)
    im = Image.new("RGBA", (r - l + 20, b - t + 20), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10 - l, 10 - t), text, font=font, fill=color, stroke_width=sw, stroke_fill=(0, 0, 0))
    return im


CAP_FONT = heavy(108)
_cap_cache = {}


def caption_sprite(words, hi):
    key = (tuple(words), tuple(sorted(hi)))
    if key in _cap_cache:
        return _cap_cache[key]
    f = CAP_FONT
    space = f.getlength(" ")
    # wrap to 2 lines within 820px
    lines, cur, cw = [], [], 0
    for w in words:
        ww = f.getlength(w.upper())
        if cur and cw + space + ww > 820:
            lines.append(cur); cur, cw = [], 0
        cur.append(w); cw += ww + (space if len(cur) > 1 else 0)
    lines.append(cur)
    lh = int(f.size * 1.02)
    im = Image.new("RGBA", (900, lh * len(lines) + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for li, line in enumerate(lines):
        tw = sum(f.getlength(w.upper()) for w in line) + space * (len(line) - 1)
        x = (900 - tw) / 2
        for w in line:
            clean = w.strip(".,?!:").lower()
            col = ORANGE if clean in hi else WHITE
            d.text((x, 10 + li * lh), w.upper(), font=f, fill=col, stroke_width=9, stroke_fill=(0, 0, 0))
            x += f.getlength(w.upper()) + space
    _cap_cache[key] = im
    return im


def panel(im, box, alpha=150):
    ov = Image.new("RGBA", (box[2] - box[0], box[3] - box[1]), (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle([0, 0, ov.width - 1, ov.height - 1], radius=26, fill=(8, 10, 16, alpha))
    im.alpha_composite(ov, (box[0], box[1]))


class ScreenStub:
    def __init__(self, line, spec, dur):
        self.page = Image.open(spec["image"]).convert("RGB")
        self.url, self.box_a, self.box_b, self.cursor = spec["url"], spec["a"], spec["b"], spec.get("cursor")
        self.win_top, self.dur = 300, dur


def render(lines, out_mp4, cover_path, music_path, work):
    # ---------- timeline ----------
    plan = []  # (line, shot_index, t_in_line_start, shot_dur)
    g = 0.0
    line_starts = []
    for ln in lines:
        nf = int(round(ln.dur * FPS))
        ln.nf = nf
        line_starts.append(g)
        g += nf / FPS
    total = g
    # ---------- audio ----------
    n = int(total * SR) + SR
    vo = np.zeros(n, np.float32)
    for ln, st in zip(lines, line_starts):
        i = int((st + ln.lead) * SR)
        seg = ln.audio[: max(0, min(len(ln.audio), n - i))]
        vo[i:i + len(seg)] += seg
    music = load_audio(music_path)
    start = int(4 * SR)  # skip the quiet intro, start on the groove
    reps = int(np.ceil((n + start) / len(music))) + 1
    music = np.tile(music, reps)[start:start + n]
    env = np.convolve(np.abs(vo), np.ones(4410) / 4410, "same")
    talk = np.clip(env / (env.max() * 0.08 + 1e-6), 0, 1)
    duck = 0.32 - 0.20 * np.convolve(talk, np.ones(8820) / 8820, "same")
    fade = np.ones(n, np.float32)
    fl = int(1.2 * SR)
    end = int(total * SR)
    fade[end - fl:end] = np.linspace(1, 0, fl)
    fade[end:] = 0
    cuts, ticks = [], []
    for li, (ln, st) in enumerate(zip(lines, line_starts)):
        acc = 0.0
        for s in ln.shots:
            cuts.append(st + acc)
            acc += ln.dur / len(ln.shots)
        if getattr(ln, "endcard", False):
            ticks += [st + 0.4, st + 0.75, st + 1.5]
        if ln.tracker and (li == 0 or lines[li - 1].tracker != ln.tracker):
            ticks.append(st + 0.05)
        if ln.timeline and (li == 0 or lines[li - 1].timeline != ln.timeline):
            ticks.append(st + 0.4)
    M.sfx_track(cuts[1:], ticks, total, work + ".sfx.wav")
    with wave.open(work + ".sfx.wav") as w:
        sfx = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    mix = vo * 1.0 + music * duck * fade
    m = min(len(sfx), n)
    mix[:m] += sfx[:m] * 0.5
    mix = np.clip(mix, -1, 1)
    with wave.open(work + ".wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    # ---------- video ----------
    proc = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", work + ".wav",
        "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
        "-shortest", "-movflags", "+faststart", out_mp4], stdin=subprocess.PIPE)
    fidx = 0
    cover_done = False
    prev = None
    for li, (ln, st) in enumerate(zip(lines, line_starts)):
        nshots = len(ln.shots)
        per = ln.nf // nshots
        bounds = [i * per for i in range(nshots)] + [ln.nf]
        if getattr(ln, "endcard", False):
            for i in range(ln.nf):
                t = i / FPS
                fr = M3.grain(ln.frame(t, st + t).convert("RGB"), fidx)
                proc.stdin.write(fr.tobytes())
                fidx += 1
            prev = None
            continue
        screen = ScreenStub(ln, ln.screen, ln.dur) if ln.screen else None
        for si, shot in enumerate(ln.shots):
            sf = bounds[si + 1] - bounds[si]
            clip = M3.Clip(shot[0], shot[1], sf) if shot else None
            for i in range(sf):
                fi = bounds[si] + i
                t = fi / FPS
                ts = i / FPS
                gt = st + t
                if clip:
                    cf = clip.next()
                    z = 1.0 + 0.10 * (1 - ease_out(ts / 0.28)) + 0.035 * (ts / max(0.5, sf / FPS))
                    sx = 10 * math.sin(gt * 1.7) + 4 * math.sin(gt * 5.3)
                    sy = 8 * math.cos(gt * 1.3) + 3 * math.sin(gt * 4.7)
                    cw, ch = cf.size
                    vw, vh = W / z, H / z
                    left, top = (cw - vw) / 2 + sx, (ch - vh) / 2 + sy
                    im = cf.crop((int(left), int(top), int(left + vw), int(top + vh))).resize((W, H), Image.BILINEAR).convert("RGBA")
                    im.alpha_composite(M3.SHADE)
                else:
                    im = M.background(gt)
                # whip blur on the first 2 frames of a cut (not the very first)
                if clip and i < 2 and (li or si):
                    im = im.filter(ImageFilter.BoxBlur(10 if i == 0 else 4))
                if screen:
                    M3.draw_browser(im, screen, t)
                if ln.tracker:
                    M.draw_tracker(im, ln.tracker, t, prev.tracker if prev else None)
                if ln.timeline:
                    M.draw_timeline_at(im, ln.timeline, t, prev.timeline[1] if prev and prev.timeline else None, 790)
                if ln.head_items:
                    for (spr, x, y, k, strike, wlen, fs) in ln.head_items:
                        tt = (t - k * 0.09) / 0.28
                        if tt <= 0:
                            continue
                        sc = 1.4 - 0.4 * ease_back(tt)
                        s2 = spr if abs(sc - 1) < 0.01 else spr.resize((int(spr.width * sc), int(spr.height * sc)), Image.BILINEAR)
                        M.put(im, s2, int(x + spr.width / 2 - s2.width / 2), int(y + spr.height / 2 - s2.height / 2), ease_out(tt))
                        if strike:
                            p = ease_out((t - (len(ln.head_items) * 0.09 + 0.2)) / 0.25)
                            if p > 0:
                                yy = y + 10 + int(fs * 0.5)
                                ImageDraw.Draw(im).rectangle([x + 10, yy, x + 10 + int(wlen * p), yy + 12], fill=ORANGE)
                if ln.emoji_spr is not None:
                    tt = (t - 0.35) / 0.3
                    if tt > 0:
                        sc = ease_back(tt)
                        e = ln.emoji_spr
                        e2 = e.resize((max(1, int(e.width * sc)), max(1, int(e.height * sc))), Image.BILINEAR)
                        wob = 8 * math.sin(t * 7)
                        e2 = e2.rotate(wob, expand=True, resample=Image.BICUBIC)
                        M.put(im, e2, int(700 - e2.width / 2), int(ln.head_bottom + 90 - e2.height / 2) if ln.head_items else 600, 1.0)
                if ln.widget:
                    if ln.head_items:
                        widgets.draw_widget(im, ln.widget, t, 680, ln.head_bottom + 430, 0.95)
                    else:
                        widgets.draw_widget(im, ln.widget.split(':')[0], t, 250 if ln.widget.endswith(':left') else 718, 640, 0.70)
                # word-pop captions (skipped while the hook headline carries the words)
                if not ln.head_items:
                    cur = None
                    for (cs, words) in ln.chunks:
                        if t >= cs - 0.03:
                            cur = (cs, words)
                    if cur:
                        spr = caption_sprite(cur[1], ln.hi)
                        tt = (t - cur[0] + 0.03) / 0.13
                        sc = 1.22 - 0.22 * ease_out(tt)
                        s2 = spr if sc < 1.01 else spr.resize((int(spr.width * sc), int(spr.height * sc)), Image.BILINEAR)
                        cy = 1310 if ln.screen else (1110 if ln.timeline else 1010)
                        M.put(im, s2, int(W / 2 - 75 - s2.width / 2), int(cy - s2.height / 2), 1.0)
                fr = M3.grain(im.convert("RGB"), fidx)
                if not cover_done and li == 0 and t >= 1.1:
                    fr.save(cover_path, quality=92)
                    cover_done = True
                proc.stdin.write(fr.tobytes())
                fidx += 1
            if clip:
                clip.close()
        prev = ln
    proc.stdin.close()
    proc.wait()
    return total
