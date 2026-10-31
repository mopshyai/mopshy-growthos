"""Short cuts (~25-30s): brand hook + phone widget, untracked-quote contrast, tight body, spoken keyword CTA, logo end card."""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from reels4 import C, G, P, D, TL, MUSIC, NAMES
from reels3 import CASE, PRICE
from motion4 import Line, render
from endcard import EndCard
def s(*pairs):
    return [(C[a], b) for a, b in pairs]
CTA = {"mon": "CONNECT", "thu": "AUTOMATE", "sun": "RENEWAL"}
EDIT = {
 "mon": [
  dict(say="Domino's tracks a 12 dollar pizza.", shots=s(("pizza", 1.0)), head="*Domino's* tracks a $12 pizza.", widget="pizza"),
  dict(say="Your agency loses track of quotes.", shots=s(("frustrated", 1.0)), hi=["quotes."], widget="unknown"),
  dict(say="Stop buying another CRM. Connect the gaps.", shots=s(("irritated", 2.0), ("thinking", 3.0)), head="Stop buying ~another ~CRM. *Connect* *the* *gaps.*"),
  dict(say="Friday, 4:55pm, a quote lands. Who picks it up? Nobody.", shots=s(("clock", 0.3), ("office", 5.0), ("irritated", 6.0)), hi=["4:55pm,", "nobody."], tracker=(G, [1,0,0,0])),
  dict(say="Follow-up? Whoever remembers. Renewal? Sticky note.", shots=s(("typing", 2.0), ("sticky", 1.0)), hi=["whoever", "sticky", "note."], tracker=(G, [2,1,0,1])),
  dict(say="Pick the step that hurts most. Connect it. Then the next.", shots=s(("thinking", 6.0), ("wtyping", 10.0)), hi=["connect", "next."], tracker=(G, [2,2,2,2])),
  dict(say="Comment connect, and I'll show you where to start.", shots=s(("smiling", 1.0), ("thumbs", 1.0)), hi=["connect,"]),
 ],
 "thu": [
  dict(say="Amazon tells you where your 9 dollar charger is.", shots=s(("packages", 0.5)), head="*Amazon* tracks your $9 charger.", widget="package"),
  dict(say="You can't say where a quote is.", shots=s(("crumpled", 1.0)), hi=["quote"], widget="unknown:left"),
  dict(say="So we built 4 pieces for a trucking insurance broker.", shots=s(("truck", 2.0), ("truck", 9.0)), hi=["4", "pieces"]),
  dict(say="Here's the real project, on our website.", shots=[None], screen=dict(image=CASE, url="mopshy.com/case-studies/all-capital-insurance", a=(590, 690, 700), b=(630, 860, 560), cursor=((900, 1150), (700, 905))), hi=["real", "project,"]),
  dict(say="One. Every lead gets tagged. Two. Quotes go to the right carriers.", shots=s(("wtyping", 5.0), ("truck", 12.0)), hi=["tagged.", "carriers."], tracker=(P, [2,1,0,0])),
  dict(say="Three. Follow-up that pings the rep. Four. A weekly dashboard.", shots=s(("recep", 6.0), ("owner", 3.0)), hi=["pings", "dashboard."], tracker=(P, [2,2,2,1])),
  dict(say="Comment automate, and I'll send you the breakdown.", shots=s(("excited", 10.0), ("thumbs", 2.0)), hi=["automate,"]),
 ],
 "sun": [
  dict(say="FedEx tracks a 10 dollar envelope.", shots=s(("envelopes", 0.5)), head="*FedEx* tracks a $10 envelope.", widget="envelope"),
  dict(say="Your agency loses track of renewal documents.", shots=s(("frustrated", 7.0)), hi=["renewal", "documents."], widget="unknown"),
  dict(say="Loss runs, the dec page, and the one nobody automates: the client's own updates.", shots=s(("manphone", 10.0), ("wtyping", 15.0), ("thinking", 12.0)), hi=["nobody", "updates."], tracker=(D, [2,2,1])),
  dict(say="At 60 days out, the client gets one list and one upload link.", shots=s(("clock", 1.0), ("smiling", 4.0)), hi=["60", "days", "one"], timeline=(TL, 0)),
  dict(say="Reminders on day 3 and day 7. Then a call, only about what's left.", shots=s(("watch", 6.0), ("recep", 9.0)), hi=["3", "7.", "only"], timeline=(TL, 3)),
  dict(say="We build that as a Workflow Sprint.", shots=[None], screen=dict(image=PRICE, url="mopshy.com/pricing", a=(0, 160, 1280), b=(20, 700, 660), cursor=((900, 1100), (300, 1000))), hi=["workflow", "sprint."]),
  dict(say="Comment renewal, and I'll send you the checklist.", shots=s(("excited", 15.0), ("thumbs", 4.0)), hi=["renewal,"]),
 ],
}
if __name__ == "__main__":
    if sys.argv[1] == "jobs":
        json.dump([[f"vo5/{k}_{i:02d}", d["say"]] for k, L in EDIT.items() for i, d in enumerate(L)], open(os.path.join(HERE, "vo5_jobs.json"), "w"))
        sys.exit()
    OUT = sys.argv[1]
    for k in sys.argv[2:]:
        lines = []
        for i, spec in enumerate(EDIT[k]):
            spec = dict(spec); say = spec.pop("say")
            lines.append(Line(say, os.path.join(HERE, f"vo5/{k}_{i:02d}"), **spec))
        lines.append(EndCard(CTA[k], dur=3.0))
        t0 = time.time()
        tot = render(lines, os.path.join(OUT, NAMES[k] + ".mp4"), os.path.join(OUT, NAMES[k] + "-cover.jpg"), MUSIC, os.path.join(HERE, k + "_v5"))
        print(k, round(tot, 1), "s in", round(time.time() - t0), "s")
