"""Logic tests: parser verdicts, simulator solutions, traps. Run: python3 test/logic.py"""
import json, pathlib, sys
from playwright.sync_api import sync_playwright
root = pathlib.Path(__file__).resolve().parent.parent
JS = r"""
() => {
  const A = window.AFLYT, out = {fail: [], info: {}};
  const run = (N, lines) => { const ctx = {}; const os = lines.map(l => A.parseOrder(l, N, ctx)); return {os, sim: A.simulate(N, os)}; };
  // 1. every night, many seeds: the reference solution wins silently
  for (const id of [1,2,3]) for (let s = 1; s <= 300; s++) {
    const N = A.makeNight(id, s, {}); const {os, sim} = run(N, N.solution);
    if (os.some(o => !o.ok)) out.fail.push(`night ${id} seed ${s}: solution not ok: ${JSON.stringify(os.map(o=>[o.text,o.errs,o.notes,o.unknown]))}`);
    if (!sim.end.win || sim.alarm) out.fail.push(`night ${id} seed ${s}: solution lost ${JSON.stringify(sim.end)} alarm ${sim.alarm} ${JSON.stringify(N.facts)}`);
    const d = run(N, [N.draft]); if (d.sim.end.win) out.fail.push(`night ${id} seed ${s}: draft wins`);
  }
  const T = A.makeNight(1, 5, {tutorial: true});
  { const {sim} = run(T, ['Om tre minutter Ida går til posthuset.']); out.info.tutDraft = [sim.alarm, sim.end]; if (sim.alarm !== 1) out.fail.push('tutorial draft should be seen once'); }
  // 2. alternative valid solutions
  const alt1 = ['Ida går til posthuset om to minutter for at hente nøglen.', 'Derefter går hun tilbage til bilen.'];
  const alt2 = ['Om to minutter henter Ida nøglen.', 'Så går hun tilbage til bilen.'];
  const alt3 = ['Ida venter i to minutter.', 'Derefter henter hun nøglen.', 'Derefter går hun hen til bilen.'];
  const alt4 = ['Kl. 22.02 går Ida til posthuset for at hente nøglen', 'bagefter går hun tilbage til bilen'];
  const alt5 = ['Om to minutter går Ida til posthuset, for at hente nøglen.', 'Derefter går Ida tilbage til bilen.'];
  for (const L of [alt1, alt2, alt3, alt4, alt5]) { const {os, sim} = run(T, L); if (!sim.end.win || sim.alarm || os.some(o=>!o.ok)) out.fail.push('alt failed: ' + L.join(' | ') + ' ' + JSON.stringify([sim.end, sim.alarm, os.map(o=>[o.ok,o.unknown,o.errs.map(e=>e.code)])])); }
  // 3. error detection (expected code)
  const N2 = A.makeNight(2, 7, {}); const N3 = A.makeNight(3, 7, {});
  const cases = [
    [T,'Om tre minutter Ida går til posthuset.','v2'], [T,'Ida gik til posthuset.','past'], [T,'Ida gå til posthuset.','inf'],
    [T,'Ida går til posthus.','bare'], [T,'Ida går til posthusen.','gender'], [T,'Ida henter nøgle.','bare'], [T,'Ida henter nøglet.','gender'],
    [T,'Ida går til posthuset for at henter nøglen.','forat'], [T,'For tre minutter siden gik Ida til posthuset.','siden'],
    [T,'I tre minutter går Ida til posthuset.','idur'], [N2,'Bo går til kiosken i Molevej.','prep'], [N2,'Bo går til kiosken på Lygtegade.','prep'],
    [N3,'Da vagten gik, gik Ida til caféen.','da'], [N3,'Når vagten går, Ida går til caféen.','v2'], [T,'Derefter hun går til bilen.','v2'],
    [T,'Ida henter et nøgle.','art']
  ];
  for (const [N, s, code] of cases) { const o = A.parseOrder(s, N, {}); const codes = o.errs.map(e => e.code);
    if (o.unknown || !codes.includes(code)) out.fail.push(`expected ${code}: "${s}" got ${o.unknown?'UNKNOWN':JSON.stringify(codes)}`);
    const fix = A.corrected(o); const fo = fix && A.parseOrder(fix, N, {}); if (!fix || !fo.ok) out.fail.push(`bad correction for "${s}": ${fix}`);
    else (out.info.fixes = out.info.fixes || []).push(s + '  →  ' + fix); }
  // 4. valid sentences must never be flagged
  const valid = [[T,'Ida går til posthuset.'],[T,'Nu går Ida til posthuset.'],[T,'Om et minut går Ida til bageren.'],[T,'Ida går hen til kiosken.'],
    [T,'Ida går ind i posthuset.'],[T,'Ida tager nøglen.'],[T,'Ida henter nøglen i posthuset.'],[T,'Ida går til Lygtegade.'],[T,'Ida henter en nøgle.'],
    [N2,'Bo henter nøglen i kiosken på Molevej.'],[N2,'Om tre minutter går Bo til kiosken på Molevej.'],[N2,'Bo går til kiosken i Lygtegade.'],
    [N3,'Når telefonen ringer, går Ida til caféen.'],[N3,'Ida går til caféen, når vagten går.'],[N3,'Når vagten går til kiosken, henter Ida nøglen.'],
    [T,'om 2 minutter går ida til posthuset'],[T,'Ida går til posthuset klokken 22.04.']];
  for (const [N, s] of valid) { const o = A.parseOrder(s, N, {}); if (!o.ok) out.fail.push(`valid flagged: "${s}" ${o.unknown?'UNKNOWN':JSON.stringify(o.errs.map(e=>e.code))} ${o.nop||''}`); }
  // 5. traps behave literally
  { const {sim} = run(N2, ['Bo henter en nøgle.', 'Derefter går han tilbage til bilen.']); out.info.decoy = sim.end; if (sim.end.why !== 'wrongkey') out.fail.push('decoy trap: ' + JSON.stringify(sim.end)); }
  { const {sim} = run(N2, ['Om tre minutter henter Bo nøglen i kiosken.', 'Derefter går han tilbage til bilen.']); out.info.nearestKiosk = [sim.end, sim.log.filter(e=>e.k==='nokey').length]; }
  // 6. night 3: a fixed time works only sometimes
  let wins = 0; for (let s = 1; s <= 300; s++) { const N = A.makeNight(3, s, {}); const {sim} = run(N, ['Om tre minutter går Ida til caféen for at hente nøglen.', 'Derefter går hun tilbage til bilen.']); if (sim.end.win && !sim.alarm) wins++; }
  out.info.night3TimeWinRate = wins / 300;
  return out;
}
"""
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto((root / "index.html").as_uri()); pg.wait_for_timeout(300)
    res = pg.evaluate(JS); b.close()
print(json.dumps(res["info"], ensure_ascii=False, indent=1))
print("PAGE ERRORS", errs)
print("FAILURES", len(res["fail"]))
for f in res["fail"][:40]: print(" -", f)
sys.exit(1 if res["fail"] or errs else 0)
