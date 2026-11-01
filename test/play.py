"""Plays all six scenes (missing on purpose a few times), the miss rounds, the repeat round and every quick game. Run: python3 test/play.py [shots]"""
import pathlib, sys, itertools
from playwright.sync_api import sync_playwright
root = pathlib.Path(__file__).resolve().parent.parent
out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/scenes"); out.mkdir(parents=True, exist_ok=True)
errs = []; shot = set()
def snap(pg, name):
    if name not in shot: shot.add(name); pg.wait_for_timeout(250); pg.screenshot(path=str(out / f"{name}.png"))
def solve_map(b):
    lots = [(c, r) for c in range(3) for r in range(2) if [c, r] not in [v[:2] for v in b["fixed"].values()]]
    for combo in itertools.permutations(lots, len(b["items"])):
        pos = {it[0]: list(p) for it, p in zip(b["items"], combo)}; pos.update({k: v[:2] for k, v in b["fixed"].items()})
        ok = all((pos[a][0] == pos[z][0] and pos[a][1] != pos[z][1]) if rel == "overfor" else (pos[a][1] == pos[z][1] and abs(pos[a][0] - pos[z][0]) == 1) for a, rel, z, _ in b["clues"])
        if ok: return dict(zip([it[0] for it in b["items"]], combo))
def answer(pg, b):
    t = b["p"]
    if t in ("choose", "listen"): pg.click(f".opt[data-k='{b['ok']}']")
    elif t == "order":
        target = [w.lower() for w in b["answers"][0][1]]; pieces = [w.lower() for w in b["pieces"]]; used = set()
        for w in target:
            k = next(k for k, x in enumerate(pieces) if x == w and k not in used); used.add(k); pg.click(f".pieces .pc[data-k='{k}']")
    elif t == "sort":
        for _ in range(len(b["items"])):
            w = pg.inner_text("#cd"); j = next(it[1] for it in b["items"] if it[0] == w); pg.click(f".bin[data-j='{j}']"); pg.wait_for_timeout(320)
    elif t == "map":
        sol = solve_map(b)
        for nm, (c, r) in sol.items(): pg.click(f".chip[data-it='{nm}']"); pg.click(f".lot[data-c='{c}'][data-r='{r}']")
        snap(pg, "map"); pg.click("#ck")
    elif t == "timeline":
        for nm, v in b["items"]: pg.click(f".chip[data-it='{nm}']"); pg.click(f".tk[data-t='{v}']")
        snap(pg, "timeline"); pg.click("#ck")
    elif t == "clock": snap(pg, "clock"); pg.click(f".clock button[data-h='{b['ok']}']")
    elif t == "hunt":
        snap(pg, "hunt")
        for o in b["targets"]:
            bb = pg.locator(f"#still [data-o='{o}']").bounding_box(); pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] * 0.7); pg.wait_for_timeout(500)
with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto((root / "index.html").as_uri()); pg.wait_for_timeout(300); snap(pg, "0-home")
    pg.click(".sc[data-k='0']"); wrong = 0; scenes = 0
    for step in range(900):
        pg.wait_for_timeout(30)
        if pg.query_selector("#nx"): pg.click("#nx"); continue
        if pg.query_selector("#ek"): snap(pg, f"end-{scenes}"); pg.click("#ek"); continue
        if pg.query_selector("#mn"):
            scenes += 1
            if scenes == 6: break
            pg.click("#mn"); continue
        b = pg.evaluate("ST.review?null:(ST.sc?ST.sc.beats[ST.i]:null)")
        if b is None:
            b = pg.evaluate("(()=>{const q=document.querySelector('.q');if(!q)return null;const t=q.childNodes[0].textContent.trim();return SCENES.flatMap(s=>s.beats).find(x=>x.p&&x.q&&x.q.trim()===t)})()")
        if not b or not b.get("p"): continue
        if wrong < 3 and b["p"] == "choose": pg.click(".opt[data-k='1']"); wrong += 1; snap(pg, "wrong")
        if b["p"] == "sort": snap(pg, "sort")
        answer(pg, b); pg.wait_for_timeout(380)
    print("scenes:", scenes, "stars:", pg.evaluate("ST.stars"))
    pg.click("#b-home"); pg.wait_for_timeout(200); snap(pg, "1-home-after")
    pg.click(".tab[data-t='spil']"); pg.wait_for_timeout(200); snap(pg, "2-games")
    for gi in range(6):
        pg.click(f".sc[data-g='{gi}']"); pg.wait_for_timeout(200)
        for _ in range(6):
            it = pg.evaluate("ARC().cur"); g = pg.evaluate(f"GAMES[{gi}].type")
            if g == "bins": pg.click(f".bin[data-j='{it['a']}']")
            else: pg.click(f".tk[data-t='{it['a']}']")
            pg.wait_for_timeout(450)
        if gi in (0, 5): snap(pg, f"game-{gi}")
        pg.evaluate("ARC().dur=0"); pg.wait_for_timeout(300); snap(pg, f"game-end-{gi}")
        print("game", gi, pg.inner_text("#ar .end h2")); pg.click("#hm"); pg.wait_for_timeout(150); pg.click(".tab[data-t='spil']")
    print("scrollWidth", pg.evaluate("document.documentElement.scrollWidth")); br.close()
print("ERRORS", errs); sys.exit(1 if errs else 0)
