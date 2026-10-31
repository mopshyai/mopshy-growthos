import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.environ.get("REEL_ASSETS", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets"))
BR = os.path.join(ASSETS, "broll") + "/"
SC = os.path.join(ASSETS, "screens") + "/"

G = ["Routing", "Follow-up", "Docs", "Renewal"]
P = ["Tags", "Carriers", "Follow-up", "Dashboard"]
D = ["Loss runs", "Dec page", "Client updates"]
TL = ["60 out", "Day 3", "Day 7", "Call"]
CASE = SC + "all-capital-insurance-desktop.png"
PRICE = SC + "pricing-desktop.png"

# (kind, head, say, extra)
REELS = {
 "mon": ("reel-mon-nov-2-finish-your-crm", [
  ("b", "*Domino's* tracks a $12 pizza.", "Domino's tracks a 12 dollar pizza.", dict(clip=BR+"pizza-7362641.mp4", start=1.0, hook=True)),
  ("b", "Your agency loses track of *quotes.*", "Your agency loses track of quotes.", dict(clip=BR+"office-evening-8347238.mp4", start=1.0)),
  ("t", "Stop buying ~another ~CRM. *Finish* *this* *one.*", "Stop buying another CRM. Finish this one.", dict(hook=True)),
  ("t", "The *gaps* lose quotes.", "Your CRM isn't losing quotes. The gaps between the steps are.", {}),
  ("b", "Fri *4:55pm*", "Friday, 4:55pm, a commercial auto quote lands in AgencyZoom.", dict(clip=BR+"office-evening-8347238.mp4", start=5.0)),
  ("t", "Who picks it *up?*", "Which of your 3 producers picks it up? Nobody.", dict(tracker=(G, [1,0,0,0]))),
  ("b", "Follow-up: *whoever* *remembers*", "Follow-up? Whoever remembers.", dict(clip=BR+"typing-8472307.mp4", start=2.0)),
  ("t", "Loss runs? *Chased* *by* *hand.*", "Loss runs from the prior carrier? Your CSR chases them by hand on Monday.", dict(tracker=(G, [2,2,1,0]))),
  ("b", "Renewal = *sticky* *note*", "Renewal in 60 days? Sticky note.", dict(clip=BR+"sticky-note-7581334.mp4", start=1.0)),
  ("t", "New CRM. *Same* *gaps.*", "New CRM, same gaps.", dict(tracker=(G, [2,2,2,2]))),
  ("t", "Pick *one* step.", "So pick the one step that hurts most", dict(tracker=(G, [1,0,0,0]))),
  ("t", "Automate it. *Then* *next.*", "and automate just that, then do the next one.", dict(tracker=(G, [2,1,0,0]))),
  ("b", "Which step *stalls?*", "Which step stalls in your agency? Tell me.", dict(clip=BR+"owner-laptop-12896411.mp4", start=2.0)),
  ("t", "*Finish* *it.*", "Your CRM's fine. Finish it.", dict(hook=True)),
 ]),
 "thu": ("reel-thu-nov-5-four-pieces", [
  ("b", "*Amazon* tracks your $9 charger.", "Amazon tells you where your 9 dollar charger is.", dict(clip=BR+"packages-7362808.mp4", start=0.5, hook=True)),
  ("b", "You can't say where a *quote* is.", "You can't say where a quote is.", dict(clip=BR+"packages-7362808.mp4", start=4.0)),
  ("b", "So we built *4* *pieces*", "So we built 4 pieces for a trucking insurance broker.", dict(clip=BR+"truck-33870727.mp4", start=2.0)),
  ("s", "The real *project*", "This is the real project. It's on our website.", dict(image=CASE, url="mopshy.com/case-studies/all-capital-insurance", a=(590, 690, 700), b=(610, 740, 620), cursor=((900, 1150), (700, 905)))),
  ("t", "All of it *by* *hand*", "Before, intake, follow-up and carrier quotes? All by hand.", dict(tracker=(P, [0,0,0,0]))),
  ("t", "Tags", "One. Every web lead gets tagged by fleet size and coverage type.", dict(num="01", tracker=(P, [1,0,0,0]))),
  ("t", "Carrier *requests*", "Two. Quote requests fan out to the right carriers.", dict(num="02", tracker=(P, [2,1,0,0]))),
  ("b", "Follow-up that *nudges*", "Three. Email and text follow-up. A stalled quote pings the rep.", dict(clip=BR+"typing-8472307.mp4", start=8.0, tracker=(P, [2,2,1,0]))),
  ("t", "Aging quotes, *weekly*", "Four. A weekly dashboard of aging quotes.", dict(num="04", tracker=(P, [2,2,2,1]))),
  ("s", "All 4 read the *tags*", "Pieces 2, 3 and 4 all read those tags.", dict(image=CASE, url="mopshy.com/case-studies/all-capital-insurance", a=(630, 860, 600), b=(640, 880, 500), cursor=((1000, 1150), (660, 930)))),
  ("t", "No tags = *guessing*", "Skip the tags and the rest is guessing.", dict(tracker=(P, [1,0,0,0]))),
  ("t", "Which one are you *missing?*", "Which piece is your agency missing? Comment it.", dict(tracker=(P, [2,2,2,2]))),
  ("t", "Build the *first.*", "4 pieces. Build the first.", dict(hook=True, tracker=(P, [1,0,0,0]))),
 ]),
 "sun": ("reel-sun-nov-8-renewal-docs", [
  ("b", "*FedEx* tracks a $10 envelope.", "FedEx tracks a 10 dollar envelope.", dict(clip=BR+"envelopes-7362636.mp4", start=0.5, hook=True)),
  ("b", "You lose track of *renewal* *docs.*", "Your agency loses track of renewal documents.", dict(clip=BR+"envelopes-7362636.mp4", start=4.0)),
  ("t", "Loss runs", "One. Loss runs from the prior carrier.", dict(num="01", tracker=(D, [1,0,0]))),
  ("t", "Dec page", "Two. The dec page.", dict(num="02", tracker=(D, [2,1,0]))),
  ("t", "Client *updates*", "Three. The client's own updates. New drivers, new locations, last year's payroll.", dict(num="03", tracker=(D, [2,2,1]))),
  ("b", "Chased by phone, *week* *6*", "That's the one your CSR chases by phone in week 6.", dict(clip=BR+"phone-call-7686682.mp4", start=2.0)),
  ("t", "60 days out: task *opens*", "Fix it like this. At 60 days out, the renewal task opens itself.", dict(timeline=(TL, 0))),
  ("t", "One list. *One* *link.*", "The client gets one list of what's missing, with one upload link.", dict(timeline=(TL, 0))),
  ("t", "Day 3. *Day* *7.*", "Day 3, a reminder. Day 7, another.", dict(timeline=(TL, 2))),
  ("t", "Then a call. *Gaps* *only.*", "Then your CSR calls, but only about what's left.", dict(timeline=(TL, 3))),
  ("s", "One workflow, *built*", "We build one workflow like this as a Workflow Sprint.", dict(image=PRICE, url="mopshy.com/pricing", a=(0, 160, 1280), b=(20, 700, 660), cursor=((900, 1100), (300, 1000)))),
  ("t", "Save for your *renewal* batch", "Save this for your next renewal batch.", dict(tracker=(D, [2,2,1]))),
  ("t", "Start with *#3.*", "Start with document number three.", dict(hook=True, tracker=(D, [0,0,1]))),
 ]),
}

if __name__ == "__main__":
    if sys.argv[1] == "jobs":
        jobs = []
        for k, (name, sc) in REELS.items():
            for i, s in enumerate(sc):
                jobs.append([f"vo3/{k}_{i:02d}", s[2]])
        json.dump(jobs, open(os.path.join(HERE, "vo3_jobs.json"), "w"))
        print(len(jobs)); sys.exit()
    from motion3 import BrollScene, ScreenScene, render
    from motion2 import VScene
    OUT = sys.argv[1]
    for k in sys.argv[2:]:
        name, spec = REELS[k]
        scenes = []
        for i, (kind, head, say, ex) in enumerate(spec):
            vo = os.path.join(HERE, f"vo3/{k}_{i:02d}")
            ex = dict(ex)
            if kind == "b":
                scenes.append(BrollScene(head, say, vo, ex.pop("clip"), ex.pop("start", 0.0), **ex))
            elif kind == "s":
                scenes.append(ScreenScene(head, say, vo, ex.pop("image"), ex.pop("url"), ex.pop("a"), ex.pop("b"), ex.pop("cursor", None), **ex))
            else:
                scenes.append(VScene(head, say, vo, **ex))
        if os.environ.get("TEST"):
            scenes = scenes[:int(os.environ["TEST"])]; name = "test-" + name
        t0 = time.time()
        total = render(scenes, os.path.join(OUT, name + ".mp4"), os.path.join(OUT, name + "-cover.jpg"), os.path.join(HERE, k + "_mix3.wav"))
        print(k, round(total, 1), "s in", round(time.time() - t0), "s")
