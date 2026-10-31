"""Agency Rescue, Episode 1: "The 4:55 quote". Story series render."""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from reels4 import C, B, MUSIC
import motion4 as M4
from motion4 import Line, render
from endcard import EndCard
import series as S
import fx2

C.update({k: B + v for k, v in dict(
    dana_desk="receptionist-8467633.mp4", dana_raj="dana-raj-8467629.mp4", dana_night="dana-night-phone-8468759.mp4",
    dana_tired="dana-night-tired-8468761.mp4", dana_maria="dana-maria-8467948.mp4",
    mower="landscaper-mower-12694264.mp4", field="landscaper-field-12694116.mp4").items()})


def s(*pairs):
    return [(C[a], b) for a, b in pairs]


DANA = ("DANA", "agency owner · illustrative")
RAJ = ("RAJ", "producer · illustrative")
CUST = ("THE CUSTOMER", "landscaper · 2 trucks")
T = ["Reply in 5 min", "Text 1 producer"]

EP = [
 dict(say="Friday, 4:55pm. Dana's phone buzzes. She never sees it.", shots=s(("clock", 0.3), ("dana_tired", 2.0)), hi=["4:55pm.", "never"], phone="lock"),
 dict(say="It's a quote request. A landscaping company, two trucks, needs coverage by Monday.", shots=s(("mower", 1.0), ("field", 6.0)), hi=["quote", "monday."], tag=CUST),
 dict(say="Dana runs a six-person independent agency. Three producers, one CSR, a good CRM.", shots=s(("dana_desk", 1.0), ("dana_maria", 3.0)), hi=["six-person"], tag=DANA),
 dict(say="Good team. Busy team.", shots=s(("dana_raj", 4.0)), hi=["busy"]),
 dict(say="At 5, the office locks up.", shots=s(("office", 5.0)), hi=["5,"]),
 dict(say="The request sits in a shared inbox. Nobody owns it.", shots=s(("office", 8.0)), hi=["nobody"], phone="inbox"),
 dict(say="Saturday morning, that business owner fills out two more forms. Two other agencies.", shots=s(("field", 14.0), ("typing", 3.0)), hi=["two", "agencies."]),
 dict(say="One of them calls him back in twenty minutes.", shots=s(("mower", 4.0)), hi=["twenty", "minutes."],
      bubble=("Another agency · Sat 9:12 AM", "Hi! Got your quote request. Quick question about the trucks.")),
 dict(say="Monday, 9am. Raj, Dana's producer, finally opens the email.", shots=s(("dana_raj", 20.0)), hi=["monday,", "finally"], tag=RAJ),
 dict(say="He calls. Voicemail.", shots=s(("manphone", 10.0)), hi=["voicemail."]),
 dict(say="Tuesday, he tries again. We already went with someone. Thanks though.", shots=s(("mower", 6.5)), hi=["already"],
      bubble=("The customer · Tuesday", "We already went with someone. Thanks though.")),
 dict(say="Here's the thing. Nobody at Dana's agency did anything wrong.", shots=s(("dana_night", 3.0)), hi=["nobody", "wrong."]),
 dict(say="There was just no step for Friday at 4:55.", shots=s(("dana_tired", 10.0)), hi=["no", "step"]),
 dict(say="So what would we build first? Not a new CRM. One rule.", shots=s(("dana_maria", 10.0)), hi=["one", "rule."], chapter="THE FIX"),
 dict(say="Every after-hours quote gets a reply in five minutes, and one named producer gets a text.", shots=s(("dana_desk", 6.0), ("dana_raj", 34.0)), hi=["five", "minutes,", "text."], checklist=("After-hours rule", ["Reply in 5 minutes", "Text 1 named producer"])),
 dict(say="That's it. That's episode one.", shots=s(("dana_maria", 15.0)), hi=["one."]),
 dict(say="Tomorrow, Raj gets that text. But does anyone actually own the lead?", shots=s(("dana_raj", 40.0)), hi=["own", "lead?"], chapter="TOMORROW"),
 dict(say="Comment automate if your Fridays look like Dana's.", shots=s(("dana_night", 12.0)), hi=["automate"]),
]


ROWS = [("Landscaping Co.", "Quote request: 2 trucks", "Need coverage by Monday. Can…", "Fri", True),
        ("Carrier portal", "Policy documents ready", "Your documents are available…", "Fri", False),
        ("Maria", "Re: Renewal list", "Here are this month's renewals…", "Thu", False),
        ("Newsletter", "Weekly update", "This week in independent…", "Thu", False)]


def overlay(im, ln, t, gt, total):
    fx2.draw_progress(im, min(1.0, gt / total))
    S.draw_label(im, gt)
    ph = getattr(ln, "phone", None)
    if ph == "lock":
        fx2.draw_phone(im, "lock", t, cx=760, cy=700, scale=0.8, buzz_at=0.7)
    elif ph == "inbox":
        fx2.draw_phone(im, "inbox", t, cx=700, cy=680, scale=0.82, rows=ROWS, hours=64)
    if getattr(ln, "checklist", None):
        fx2.draw_checklist(im, ln.checklist[0], ln.checklist[1], t)
    if ln.tag:
        fx2.draw_tag(im, ln.tag, t)
    if ln.bubble:
        fx2.draw_bubble(im, ln.bubble, t)
    if ln.chapter:
        fx2.draw_chapter(im, ln.chapter, t, kicker="EPISODE 1" if ln.chapter == "THE FIX" else "UP NEXT")


def captions(im, ln, t):
    fx2.draw_captions(im, ln, t, cy=1300 if getattr(ln, "phone", None) else 1030)


NAME = "agency-rescue-ep01-the-455-quote"
if __name__ == "__main__":
    if sys.argv[1] == "jobs":
        json.dump([[f"vo_ep1/l{i:02d}", d["say"]] for i, d in enumerate(EP)], open(os.path.join(HERE, "vo_ep1_jobs.json"), "w")); sys.exit()
    OUT = sys.argv[1]
    M4.OVERLAY = overlay
    M4.CAPTION_FN = captions
    lines = [S.StingCard("Agency Rescue", 1, "The 4:55 quote")]
    for i, spec in enumerate(EP):
        spec = dict(spec); say = spec.pop("say")
        lines.append(Line(say, os.path.join(HERE, f"vo_ep1/l{i:02d}"), **spec))
    lines.append(EndCard("AUTOMATE", dur=3.0))
    t0 = time.time()
    tot = render(lines, os.path.join(OUT, NAME + ".mp4"), os.path.join(OUT, NAME + "-cover.jpg"), MUSIC, os.path.join(HERE, "ep1"))
    print("ep1", round(tot, 1), "s in", round(time.time() - t0), "s")
