"""Plays all six scenes, the miss round and the repeat round on a phone-sized screen. Run: python3 test/play.py [shots dir]"""
import pathlib, sys
from playwright.sync_api import sync_playwright
root = pathlib.Path(__file__).resolve().parent.parent
out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/scenes"); out.mkdir(parents=True, exist_ok=True)
errs = []
def answer(pg, b):
    if b["p"] in ("choose", "listen"): pg.click(f".opt[data-k='{b['ok']}']"); return
    target = [w.lower() for w in b["answers"][0][1]]; pieces = [w.lower() for w in b["pieces"]]; used = set()
    for w in target:
        k = next(k for k, x in enumerate(pieces) if x == w and k not in used); used.add(k); pg.click(f".pieces .pc[data-k='{k}']")
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto((root / "index.html").as_uri()); pg.wait_for_timeout(300); pg.screenshot(path=str(out / "0-menu.png"))
    pg.click(".scard[data-k='0']"); wrong = 0; scenes = 0
    for step in range(600):
        pg.wait_for_timeout(40)
        if pg.query_selector("#nx"): pg.click("#nx"); continue
        if pg.query_selector("#ek"):
            pg.screenshot(path=str(out / f"end-{scenes}.png")); pg.click("#ek"); continue
        if pg.query_selector("#mn"):
            scenes += 1
            if scenes == 6: break
            pg.click("#mn"); continue
        b = pg.evaluate("ST.review!==null&&ST.review!==undefined&&!ST.sc?null:(ST.sc?ST.sc.beats[ST.i]:null)")
        if b is None:  # in a miss round: find the puzzle by its question text
            b = pg.evaluate("(()=>{const q=document.querySelector('.q');if(!q)return null;return SCENES.flatMap(s=>s.beats).find(x=>x.p&&x.q===q.textContent)})()")
        if not b or not b.get("p"): continue
        if wrong < 3 and b["p"] == "choose":  # miss on purpose three times
            pg.click(f".opt[data-k='{1}']"); wrong += 1
            if wrong == 1: pg.wait_for_timeout(300); pg.screenshot(path=str(out / "wrong.png"))
        answer(pg, b); pg.wait_for_timeout(350)
    print("scenes finished:", scenes, "done map:", pg.evaluate("ST.done"))
    pg.click("#b-home"); pg.wait_for_timeout(200); pg.screenshot(path=str(out / "menu-after.png"))
    pg.click("#rv"); n = 0
    while n < 12 and not pg.query_selector("#mn"):
        n += 1; b = pg.evaluate("(()=>{const q=document.querySelector('.q');return SCENES.flatMap(s=>s.beats).find(x=>x.p&&q&&x.q===q.textContent)})()")
        answer(pg, b); pg.wait_for_timeout(350)
        if pg.query_selector("#nx"): pg.click("#nx")
    print("repeat round items:", n, "result:", pg.inner_text(".end h2") if pg.query_selector(".end h2") else None)
    pg.screenshot(path=str(out / "repeat-end.png"))
    print("scrollWidth", pg.evaluate("document.documentElement.scrollWidth")); br.close()
print("ERRORS", errs); sys.exit(1 if errs else 0)
