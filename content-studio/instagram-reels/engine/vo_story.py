import asyncio, json, sys, os, re
import edge_tts
VOICE, RATE = "en-US-AndrewNeural", "+6%"
FIX = {"AgencyZoom": "Agency Zoom", "4:55pm": "4:55 PM", "CSR": "C.S.R.", "CRM's": "C.R.M.'s", "CRM": "C.R.M.", "CRMs": "C.R.M.s"}
def speakable(s):
    for k, v in FIX.items():
        s = re.sub(r"(?<![\w.])" + re.escape(k) + r"(?![\w])", v, s)
    return s
async def one(text, base):
    c = edge_tts.Communicate(speakable(text), VOICE, rate=RATE, boundary="WordBoundary")
    words = []
    with open(base + ".mp3", "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append([ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7, ch["text"]])
    json.dump(words, open(base + ".json", "w"))
async def main():
    jobs = json.load(open(sys.argv[1]))
    for base, text in jobs:
        for attempt in range(4):
            if os.path.exists(base + ".mp3") and os.path.getsize(base + ".mp3") > 0:
                break
            try:
                await one(text, base)
            except Exception as e:
                print("retry", base, e)
                await asyncio.sleep(2)
asyncio.run(main())
