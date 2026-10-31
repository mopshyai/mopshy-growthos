"""'Stop calling Friday's leads back on Monday' (swipe-research Negative Command hook)."""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from reels4 import C, MUSIC
from motion4 import Line, render
from endcard import EndCard
def s(*pairs):
    return [(C[a], b) for a, b in pairs]
T = ["Capture", "Route", "Reply"]
FRI = [
 dict(say="Stop calling Friday's leads back on Monday.", shots=s(("clock", 0.5)), head="Stop calling *Friday's* leads back on *Monday.*", widget="unknown"),
 dict(say="They already bought somewhere else.", shots=s(("irritated", 2.0)), hi=["somewhere", "else."]),
 dict(say="Friday, 4:55pm. A quote lands. You close at 5.", shots=s(("office", 1.0), ("clock", 2.0)), hi=["4:55pm.", "5."]),
 dict(say="Monday, your producer calls. Voicemail.", shots=s(("manphone", 10.0)), hi=["voicemail."]),
 dict(say="The fix runs while you're closed.", shots=s(("wtyping", 3.0)), hi=["closed."], tracker=(T, [0, 0, 0])),
 dict(say="One. The form grabs everything quoting needs.", shots=s(("typing", 4.0)), hi=["everything"], tracker=(T, [1, 0, 0])),
 dict(say="Two. It texts one producer.", shots=s(("recep", 3.0)), hi=["one"], tracker=(T, [2, 1, 0])),
 dict(say="Three. Your approved reply goes out in 5 minutes.", shots=s(("smiling", 2.0)), hi=["5", "minutes."], tracker=(T, [2, 2, 1])),
 dict(say="Monday at 9? A full file.", shots=s(("thumbs", 1.0)), hi=["full", "file."], tracker=(T, [2, 2, 2])),
 dict(say="Comment automate for the setup.", shots=s(("excited", 10.0)), hi=["automate"]),
 dict(say="Stop losing Friday's leads.", shots=s(("frustrated", 2.0)), hi=["friday's"]),
]
NAME = "reel-stop-calling-fridays-leads"
if __name__ == "__main__":
    if sys.argv[1] == "jobs":
        json.dump([[f"vo6/fri_{i:02d}", d["say"]] for i, d in enumerate(FRI)], open(os.path.join(HERE, "vo6_jobs.json"), "w")); sys.exit()
    OUT = sys.argv[1]
    lines = []
    for i, spec in enumerate(FRI):
        spec = dict(spec); say = spec.pop("say")
        lines.append(Line(say, os.path.join(HERE, f"vo6/fri_{i:02d}"), **spec))
    lines.append(EndCard("AUTOMATE", dur=3.0))
    t0 = time.time()
    tot = render(lines, os.path.join(OUT, NAME + ".mp4"), os.path.join(OUT, NAME + "-cover.jpg"), MUSIC, os.path.join(HERE, "fri_v6"))
    print("fri", round(tot, 1), "s in", round(time.time() - t0), "s")
