import sys, os, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from reels3 import REELS as R3, CASE, PRICE, ASSETS
from motion4 import Line, render
from endcard import EndCard
CTA = {'mon': 'CONNECT', 'thu': 'AUTOMATE', 'sun': 'RENEWAL'}
B = os.path.join(ASSETS, "broll") + "/"
MUSIC = os.path.join(ASSETS, "music", "urban-hip-hop-beat-prettyjohn1-523746.mp3")
C = {k: B + v for k, v in dict(
    pizza="pizza-7362641.mp4", packages="packages-7362808.mp4", envelopes="envelopes-7362636.mp4",
    office="office-evening-8347238.mp4", truck="truck-33870727.mp4", phone="phone-call-7686682.mp4",
    typing="typing-8472307.mp4", sticky="sticky-note-7581334.mp4", owner="owner-laptop-12896411.mp4",
    frustrated="frustrated-laptop-12908960.mp4", watch="watch-concerned-13801280.mp4", notif="phone-notification-7822022.mp4",
    smiling="smiling-call-8037831.mp4", thumbs="thumbs-up-10373958.mp4", thinking="thinking-8731297.mp4",
    crumpled="crumpled-paper-7581228.mp4", recep="receptionist-8467633.mp4", clock="clock-11267667.mp4",
    irritated="irritated-look-8724356.mp4", excited="excited-8724462.mp4", manphone="man-office-phone-7262260.mp4",
    wtyping="woman-typing-7605074.mp4").items()}
def s(*pairs):
    return [(C[a], b) for a, b in pairs]
G = ["Routing", "Follow-up", "Docs", "Renewal"]; P = ["Tags", "Carriers", "Follow-up", "Dashboard"]
D = ["Loss runs", "Dec page", "Client updates"]; TL = ["60 out", "Day 3", "Day 7", "Call"]
EDIT = {
 "mon": [
  dict(shots=s(("pizza", 1.0)), head="*Domino's* tracks a $12 pizza.", emoji="🍕"),
  dict(shots=s(("frustrated", 1.0), ("crumpled", 0.5)), hi=["quotes."]),
  dict(shots=s(("irritated", 2.0), ("thinking", 3.0)), head="Stop buying ~another ~CRM. *Finish* *this* *one.*"),
  dict(shots=s(("wtyping", 2.0), ("watch", 1.0)), hi=["gaps"]),
  dict(shots=s(("clock", 0.3), ("notif", 0.5), ("office", 5.0)), hi=["4:55pm,", "agencyzoom."]),
  dict(shots=s(("office", 1.0), ("irritated", 6.0)), hi=["nobody."], tracker=(G, [1,0,0,0])),
  dict(shots=s(("typing", 2.0)), hi=["whoever", "remembers."]),
  dict(shots=s(("manphone", 3.0), ("recep", 2.0)), hi=["hand"], tracker=(G, [2,2,1,0])),
  dict(shots=s(("sticky", 1.0)), hi=["sticky", "note."], tracker=(G, [2,2,2,1])),
  dict(shots=s(("frustrated", 5.0)), hi=["same", "gaps."], tracker=(G, [2,2,2,2])),
  dict(shots=s(("thinking", 6.0)), hi=["one"], tracker=(G, [1,0,0,0])),
  dict(shots=s(("wtyping", 10.0), ("notif", 2.0)), hi=["next"], tracker=(G, [2,1,0,0])),
  dict(shots=s(("smiling", 1.0), ("excited", 3.0)), hi=["stalls"]),
  dict(shots=s(("thumbs", 1.0)), hi=["finish"], emoji_end="✅"),
 ],
 "thu": [
  dict(shots=s(("packages", 0.5)), head="*Amazon* tracks your $9 charger.", emoji="📦"),
  dict(shots=s(("watch", 2.0), ("irritated", 8.0)), hi=["quote"]),
  dict(shots=s(("truck", 2.0), ("truck", 9.0)), hi=["4", "pieces"]),
  dict(shots=[None], screen=dict(image=CASE, url="mopshy.com/case-studies/all-capital-insurance", a=(590, 690, 700), b=(610, 740, 620), cursor=((900, 1150), (700, 905))), hi=["real", "project."]),
  dict(shots=s(("crumpled", 2.0), ("frustrated", 4.0)), hi=["hand."], tracker=(P, [0,0,0,0])),
  dict(shots=s(("notif", 1.0), ("wtyping", 5.0)), hi=["tagged"], tracker=(P, [1,0,0,0])),
  dict(shots=s(("typing", 6.0), ("truck", 12.0)), hi=["right", "carriers."], tracker=(P, [2,1,0,0])),
  dict(shots=s(("notif", 3.0), ("recep", 6.0)), hi=["pings"], tracker=(P, [2,2,1,0])),
  dict(shots=s(("owner", 3.0)), hi=["weekly"], tracker=(P, [2,2,2,1])),
  dict(shots=[None], screen=dict(image=CASE, url="mopshy.com/case-studies/all-capital-insurance", a=(630, 860, 600), b=(640, 880, 500), cursor=((1000, 1150), (660, 930))), hi=["tags."]),
  dict(shots=s(("thinking", 9.0)), hi=["guessing."], tracker=(P, [1,0,0,0])),
  dict(shots=s(("excited", 10.0), ("smiling", 3.0)), hi=["missing?"]),
  dict(shots=s(("thumbs", 2.0)), hi=["first."]),
 ],
 "sun": [
  dict(shots=s(("envelopes", 0.5)), head="*FedEx* tracks a $10 envelope.", emoji="✉️"),
  dict(shots=s(("frustrated", 7.0), ("crumpled", 4.0)), hi=["renewal", "documents."]),
  dict(shots=s(("manphone", 10.0)), hi=["loss", "runs"], tracker=(D, [1,0,0])),
  dict(shots=s(("wtyping", 15.0)), hi=["dec", "page."], tracker=(D, [2,1,0])),
  dict(shots=s(("notif", 2.0), ("owner", 6.0), ("thinking", 12.0)), hi=["updates."], tracker=(D, [2,2,1])),
  dict(shots=s(("phone", 2.0), ("manphone", 18.0)), hi=["phone"]),
  dict(shots=s(("clock", 1.0), ("notif", 4.0)), hi=["60", "days"], timeline=(TL, 0)),
  dict(shots=s(("smiling", 4.0)), hi=["one"], timeline=(TL, 0)),
  dict(shots=s(("notif", 5.0), ("watch", 6.0)), hi=["3,", "7,"], timeline=(TL, 2)),
  dict(shots=s(("recep", 9.0)), hi=["only"], timeline=(TL, 3)),
  dict(shots=[None], screen=dict(image=PRICE, url="mopshy.com/pricing", a=(0, 160, 1280), b=(20, 700, 660), cursor=((900, 1100), (300, 1000))), hi=["workflow", "sprint."]),
  dict(shots=s(("excited", 15.0)), hi=["save"]),
  dict(shots=s(("thumbs", 4.0)), hi=["three."]),
 ],
}
NAMES = {k: v[0] for k, v in R3.items()}
if __name__ == "__main__":
    OUT = sys.argv[1]
    for k in sys.argv[2:]:
        lines = []
        for i, (spec, r3) in enumerate(zip(EDIT[k], R3[k][1])):
            spec = dict(spec); spec.pop("emoji_end", None)
            lines.append(Line(r3[2], os.path.join(HERE, f"vo4/{k}_{i:02d}"), **spec))
        lines.append(EndCard(CTA[k]))
        name = NAMES[k]
        if os.environ.get("TEST"):
            lines = lines[:int(os.environ["TEST"])]; name = "test-" + name
        t0 = time.time()
        tot = render(lines, os.path.join(OUT, name + ".mp4"), os.path.join(OUT, name + "-cover.jpg"), MUSIC, os.path.join(HERE, k + "_v4"))
        print(k, round(tot, 1), "s in", round(time.time() - t0), "s")
