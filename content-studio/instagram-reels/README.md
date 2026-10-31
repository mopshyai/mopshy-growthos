# Instagram reels studio

How Mopshy plans, writes and renders Instagram reels: the process, the style rules the founder approved, and the code that renders them. Built and approved on 2026-10-31.

This folder is a content tool, not an agent. It does not post, schedule or message anyone. Every output is a draft for founder review.

## The approved style

These rules come from four rounds of founder feedback. Static text cards and a cartoon mascot were both rejected as looking AI-made. The fast-cut, real-people version was approved.

| Element | Rule |
|---|---|
| Length | 20–30s of content plus a 3s end card. 43s was too long for non-follower reach. |
| Hook | Famous-brand comparison as **text only**, e.g. "Domino's tracks a $12 pizza. Your agency loses track of quotes." **No third-party logos**, because of takedown risk. Score every hook with `hookscore.py`; aim for 80+. |
| Visuals | Real-people stock b-roll. A new shot every 1–2s, each with a punch-in zoom, a whip blur on the cut and a slight handheld drift. Light grain. |
| Captions | Big 2–3 word pops, heavy font with a black stroke. Key words in Mopshy orange (#FF6531). |
| Overlays | Frosted-glass step cards (tracker) and a checkmark timeline. Phone widgets in Mopshy colors with generic labels: order tracker, package map, envelope status, and an untracked quote showing "Status: ???". |
| Proof | Real screens from mopshy.com (case study, pricing) in a browser frame with a moving cursor. Never show unmeasured metrics. |
| Voice | edge-tts `en-US-AndrewNeural`, rate +14%. Word timings drive the captions. |
| Music | One non-Content-ID royalty-free beat, ducked under the voice and faded on the end card. |
| Close | Always the animated logo end card. The tile pops in, the lines draw, the nodes pop and the ring pulses. Then the MOPSHY AI wordmark and a pulsing **COMMENT KEYWORD** pill (AUTOMATE / CONNECT / …). Say the keyword out loud in the last line too. |
| Loop | The last spoken line echoes a word from the hook. |

Never use: mascots or cartoon characters, static text-card reels, client logos without written permission, invented metrics, or stock clips with distracting on-screen text (e.g. a phone showing a bank fraud alert).

## Realistic UI (v2, approved 2026-10-31)

`engine/fx2.py` sets every overlay in Apple's SF Pro system font and copies real phone UI, with no third-party app logos.

| Element | What it looks like | Function |
|---|---|---|
| Captions (default for all reels) | Karaoke style. Each word pops in as it's spoken, the current word sits on an orange box, key words are orange, soft shadow. | `draw_captions` |
| iPhone | Titanium frame, Dynamic Island, side buttons. Springs in with a tilt. | `draw_phone(kind="lock" or "inbox")` |
| Lock screen | Big clock, then a Mail-style notification drops in with a buzz shake and vibration lines | `draw_phone("lock", notif=(title, body))` |
| Shared inbox | Mail-style list, unread row highlighted, orange "Unassigned" tag, "Unread for N hours" counter ticking up | `draw_phone("inbox", rows=[…], hours=N)` |
| Text message | iMessage grey bubble. Typing dots first, then the message, then "Delivered". | `draw_bubble((who, text))` |
| Name tag | Broadcast lower-third: orange bar drops, white card wipes in, name slides up | `draw_tag((name, role))` |
| Checklist | Reminders-style card whose checkmarks draw themselves and whose counter ticks | `draw_checklist(title, items)` |
| Chapter card | Cinematic letterbox bars, kicker line, big title, orange underline | `draw_chapter(text, kicker=…)` |
| Progress bar | Thin bar with a glowing head | `draw_progress(frac)` |

## Story series: "Agency Rescue"

Daily 60–90s episodes about a composite independent agency, labelled "Illustrative story · composite agency" for the first 5 seconds and in the caption. No invented results, ever.

- **Cast:** Dana (owner), Raj (producer) and Maria (CSR) all come from one cottonbro studio shoot on Pexels, so the faces stay consistent. The customer is a landscaper. The clip IDs are in `fetch_assets.sh`.
- **Episode shape:**
  - 0–3s: cold open, mid-scene.
  - Then: who it is and what's at stake, and how it gets worse.
  - "THE FIX": chapter card plus checklist.
  - Then: the lesson.
  - "UP NEXT": the cliffhanger.
  - Last: the logo end card with COMMENT KEYWORD.
- **Voice:** `vo_story.py` (AndrewNeural +6%, calmer than the reels' +14%).
- **Build an episode:** copy `ep1.py`. Each line takes the usual fields, plus `phone` ("lock" or "inbox"), `bubble`, `tag`, `checklist` and `chapter`. `series.StingCard` opens the episode and `EndCard` closes it.

```bash
python3 ep1.py jobs
uv run --with edge-tts==7.3.1 python vo_story.py vo_ep1_jobs.json
python3 ep1.py ./        # agency-rescue-ep01-the-455-quote.mp4
```

## Process

1. **Plan the week:** 4–5 posts, at least 3 of them reels, on one market track. The insurance and HVAC tracks never share prices, claims or proof.
2. **Research:** about once a month, rank creators' Shorts by views divided by that channel's own median, read the spoken first 3 seconds, and note which hook shapes over-index. On 2026-10-31 the winners were real-conversation cold-opens, hyper-specific operating details, and "agency owner" callouts. The sample was small, so confidence is low.
3. **Script:** write three hooks from different formulas, score them, and pick the best. Time the script with `beats.py`; no beat should run over 4s. Check that it reads as human.
4. **Claims check:** use only claims allowed by the public claims register (`docs/public-claims-register.md` in mopshy-ai-growth-engine). Quote prices exactly from the brief. Real client work is limited to the published case studies.
5. **Render:** use `engine/`. Check sample frames and the end card before sending.
6. **Caption:** one ask that matches the end-card keyword, and up to 3 hashtags. Prepare the reply asset (checklist, breakdown or workflow review link) before posting, and reply the same day.
7. **Measure:** 48 hours after posting, record the 3s hold, average watch time vs length, non-follower reach, sends and comments.

## Render a reel

Requirements: Python 3.14 with Pillow and numpy, ffmpeg, Google Chrome (for site screenshots) and `uv` (to run edge-tts 7.3.1).

```bash
cd content-studio/instagram-reels
./fetch_assets.sh                      # b-roll, music and site screenshots
cd engine
python3 reels6.py jobs                 # writes the voice-line job list
uv run --with edge-tts==7.3.1 python vo4.py vo6_jobs.json
python3 reels6.py ./                   # renders reel-stop-calling-fridays-leads.mp4 + cover
```

To make a new reel, copy `reels6.py` and edit the line list. Each line has:
- `say`: the spoken text.
- `shots`: (clip, start-second) pairs, cut evenly across the line.
- Optional `head`: hook headline. Wrap a word in `*word*` for orange or `~word~` for strike-through.
- Optional `hi`: words to color orange in the captions.
- Optional `tracker`: (labels, states), where 0 is upcoming, 1 is active and 2 is done.
- Optional `timeline`, `widget` (`pizza`, `package`, `envelope`, `unknown`, or `unknown:left`) and `screen` (a site screenshot with pan boxes and a cursor).

End every reel with `EndCard("KEYWORD")`.

| File | What it does |
|---|---|
| `motion4.py` | Fast-cut renderer: b-roll streaming, zoom punches, captions (`CAPTION_FN`), per-frame `OVERLAY` hook, audio mix (voice + ducked music + SFX) |
| `fx2.py` | Realistic UI v2 (see above) |
| `series.py`, `ep1.py`, `vo_story.py` | Story-series sting, label, Episode 1 spec and story-pace voice |
| `ui2.py` | Frosted step cards and checkmark timeline |
| `widgets.py` | Phone screens used in hooks |
| `endcard.py` | Animated vector logo end card with the keyword CTA |
| `motion.py`, `motion2.py`, `motion3.py`, `mascot.py` | Shared helpers: fonts, easing, background, browser frame, grain. The mascot is retired but still imported. |
| `reels3.py` to `reels6.py` | Scripts and shot lists for the Nov 2 week and the Friday-leads reel |
| `vo4.py` | edge-tts voice generation with per-word timings and retries |

## Assets and licenses

- `assets/brand/mopshy-logo-icon.png` is the official logo, supplied by the founder on 2026-10-31. Use it on every reel and visual.
- B-roll: Pexels free license (commercial use, no credit required). The Pexels video IDs are listed in `fetch_assets.sh`.
- Music: "Urban Hip-Hop Beat" by prettyjohn1, Pixabay Content License, checked as not Content ID registered on 2026-10-31.
- Neither the b-roll nor the music is committed, because the licenses don't allow re-hosting the raw files.

## Open items

- Link @mopshy.ai to Meta Insights so watch time and non-follower reach can be read.
- The founder must approve naming All Capital Insurance on Instagram.
- A/B test the voicemail cold-open hook (dramatization, labelled) against the Negative Command hook.
