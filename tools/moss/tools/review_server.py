"""Listening page for the clips on the review list (E:\\gc-audio\\qa_review.tsv, rows after the last "USER REVIEWED
ALL" marker; English pace-only rows are left out: they were false alarms). Notes are saved automatically to
E:\\gc-audio\\_test\\qa\\review_notes.json.  Run:  python review_server.py   then open http://127.0.0.1:8765/"""
import html, json, re, sys, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path("E:/gc-audio")
NOTES = ROOT / "_test" / "qa" / "review_notes.json"
REPOS = ("gc-audio-science", "gc-audio-humanities", "gc-audio-lang-math")
B = "https://shanchuan.org/middle/readaloud/"


def build():
    lines = (ROOT / "qa_review.tsv").read_text(encoding="utf-8").splitlines()
    mark = max(i for i, l in enumerate(lines) if "USER REVIEWED ALL" in l)
    rows = {}
    for l in lines[mark + 1:]:
        p = l.split("\t")
        if len(p) < 9 or p[1] not in REPOS:
            continue
        date, repo, lesson, lang, key, f0, pace, reasons, tries = p[:9]
        if lang == "en" and reasons.startswith("pace"):
            continue                                   # digits/degree signs counted as written: false alarms
        rows[(repo, lesson, lang, key)] = dict(date=date, repo=repo, lesson=lesson, lang=lang, key=key, f0=f0,
                                               pace=pace, reasons=reasons, tries=tries)
    texts = {}
    for lesson in sorted({r["lesson"] for r in rows.values()}):
        try:
            t = json.loads(urllib.request.urlopen(B + ("shared" if lesson == "_shared" else lesson) + ".json",
                                                  timeout=60).read().decode("utf-8"))
            for c in t["clips"]:
                texts[(lesson, c["lang"], c["key"])] = c["send"]
        except Exception:                              # noqa: BLE001
            pass
    out = []
    for r in rows.values():
        r["text"] = texts.get((r["lesson"], r["lang"], r["key"]), "(text no longer in the transcript)")
        r["id"] = f'{r["repo"]}/{r["lesson"]}/{r["lang"]}/{r["key"]}'
        r["exists"] = (ROOT / r["repo"] / r["lesson"] / r["lang"] / f'{r["key"]}.mp3').exists()
        m = re.search(r"F0 (\d+)", r["reasons"])
        r["kind"] = ("音高偏高" if m and int(m.group(1)) > 300 else "音高偏低" if m else
                     "偏慢" if "pace" in r["reasons"] and float(r["pace"] or 0) < 3.5 else
                     "偏快" if "pace" in r["reasons"] else "其他")
        out.append(r)
    order = {"音高偏高": 0, "偏快": 1, "偏慢": 2, "音高偏低": 3, "其他": 4}
    out.sort(key=lambda r: (order[r["kind"]], r["lesson"], r["key"]))
    return out


PAGE = r"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>复听清单</title><style>
:root{--bg:#fafaf7;--fg:#1d1d1b;--muted:#6b6b66;--line:#e3e2dc;--card:#fff;--acc:#2f6f5e;--bad:#9b2c2c}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--fg:#ecebe6;--muted:#9a9993;--line:#2e2d2a;--card:#1f1f1d;--acc:#7cc4ad;--bad:#e58b8b}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 system-ui,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1000px;margin:0 auto;padding:20px 16px 80px}h1{font-size:21px;margin:0 0 4px}h2{font-size:16px;margin:28px 0 8px}
.sub{color:var(--muted);margin:0 0 6px}.row{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin:8px 0}
.meta{color:var(--muted);font-size:12px}.text{margin:4px 0 8px}audio{height:32px;width:100%;max-width:420px}
.ctl{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:6px}label{cursor:pointer}
textarea{width:100%;min-height:34px;font:inherit;padding:5px 8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg)}
.keep{color:var(--acc)}.redo{color:var(--bad)}#status{position:fixed;right:16px;bottom:12px;background:var(--card);border:1px solid var(--line);border-radius:6px;padding:4px 10px;font-size:13px;color:var(--muted)}
.player{display:flex;align-items:center;gap:10px;flex-wrap:wrap}.ctl .tag{font-size:14px;padding:3px 14px}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 6px}.tag{font:inherit;font-size:13px;padding:2px 10px;border-radius:14px;border:1px solid var(--line);background:var(--bg);color:var(--fg);cursor:pointer}
.tag.on{background:var(--bad);border-color:var(--bad);color:#fff}.tag.ok.on{background:var(--acc);border-color:var(--acc)}
.bar{position:sticky;top:0;background:var(--bg);padding:8px 0;border-bottom:1px solid var(--line);z-index:1}
</style></head><body><main>
<div class="bar"><h1>复听清单</h1><p class="sub" id="summary"></p></div>
<div id="list"></div></main><div id="status">已加载</div>
<script>
const DATA = __DATA__;
const TAGS = ['幼儿音','太幼稚','大叫','有点尖','太快','太慢','有气无力','快慢不定','太造作','像方言','读错字','停顿不对'];
let NOTES = __NOTES__;
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function summary(){ const n = DATA.length, k = DATA.filter(r => NOTES[r.id]?.verdict === 'keep').length,
  d = DATA.filter(r => NOTES[r.id]?.verdict === 'redo').length;
  document.getElementById('summary').textContent = `共 ${n} 句 · 保留 ${k} · 重录 ${d} · 未定 ${n-k-d}。选择和备注自动保存。`; }
let groups = {}; DATA.forEach(r => (groups[r.kind] ||= []).push(r));
document.getElementById('list').innerHTML = Object.entries(groups).map(([kind, rs]) => `<h2>${esc(kind)}（${rs.length} 句）</h2>` + rs.map(r => {
  const nt = NOTES[r.id] || {}; const src = '/audio/' + r.repo + '/' + r.lesson + '/' + r.lang + '/' + r.key + '.mp3';
  return `<div class="row" data-id="${esc(r.id)}"><div class="meta">${esc(r.lesson)} · ${r.lang}:${r.key} · 音高 ${esc(r.f0)} Hz · 语速 ${esc(r.pace)} 字/秒 · ${esc(r.reasons)} · 试了 ${esc(r.tries)} 次</div>
  <div class="text">${esc(r.text)}</div><div class="player">${r.exists ? `<audio controls preload="none" src="${src}"></audio>` : '<div class="meta">（本地没有这个文件：可能已按新文字重录）</div>'}
</div>
  <div class="ctl"><button type="button" class="tag ok${(nt.tags||[]).includes('还行')?' on':''}" data-tag="还行">还行</button><label class="keep"><input type="radio" name="v-${esc(r.id)}" value="keep" ${nt.verdict==='keep'?'checked':''}> 保留</label>
  <label class="redo"><input type="radio" name="v-${esc(r.id)}" value="redo" ${nt.verdict==='redo'?'checked':''}> 重录</label></div>
  <div class="tags">${TAGS.map(t => `<button type="button" class="tag${(nt.tags||[]).includes(t)?' on':''}${t==='还行'?' ok':''}" data-tag="${esc(t)}">${esc(t)}</button>`).join('')}</div>
  <textarea placeholder="备注（可选）">${esc(nt.note||'')}</textarea></div>`; }).join('')).join('');
document.getElementById('list').addEventListener('click', e => { const b = e.target.closest('button.tag'); if (!b) return;
  const row = b.closest('.row'), id = row.dataset.id, t = b.dataset.tag; NOTES[id] = NOTES[id] || {};
  const tags = new Set(NOTES[id].tags || []); tags.has(t) ? tags.delete(t) : tags.add(t); NOTES[id].tags = [...tags];
  b.classList.toggle('on', tags.has(t));
  if (tags.has(t)) {                                   // a problem tag suggests re-recording, "还行" suggests keeping
    NOTES[id].verdict = t === '还行' ? 'keep' : 'redo';
    row.querySelector(`input[value="${NOTES[id].verdict}"]`).checked = true; }
  save(); });
let timer = null;
function save(){ clearTimeout(timer); document.getElementById('status').textContent = '保存中…';
  timer = setTimeout(() => fetch('/notes', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(NOTES)})
    .then(r => { document.getElementById('status').textContent = r.ok ? '已保存 ' + new Date().toLocaleTimeString() : '保存失败'; })
    .catch(() => document.getElementById('status').textContent = '保存失败：服务器没运行？'), 400); summary(); }
document.getElementById('list').addEventListener('change', e => { const row = e.target.closest('.row'); if (!row) return;
  const id = row.dataset.id; NOTES[id] = NOTES[id] || {}; if (e.target.type === 'radio') NOTES[id].verdict = e.target.value; save(); });
document.getElementById('list').addEventListener('input', e => { if (e.target.tagName !== 'TEXTAREA') return;
  const id = e.target.closest('.row').dataset.id; NOTES[id] = NOTES[id] || {}; NOTES[id].note = e.target.value; save(); });
summary();
</script></body></html>"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype):
        b = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            notes = json.loads(NOTES.read_text(encoding="utf-8")) if NOTES.exists() else {}
            page = PAGE.replace("__DATA__", json.dumps(DATA, ensure_ascii=False)).replace("__NOTES__", json.dumps(notes, ensure_ascii=False))
            return self.send(200, page, "text/html; charset=utf-8")
        m = re.fullmatch(r"/audio/(gc-audio-[a-z-]+)/([A-Za-z0-9_/-]+)/(en|zh)/([0-9a-f]{8})\.mp3", self.path)
        if m and m.group(1) in REPOS:
            f = ROOT / m.group(1) / m.group(2) / m.group(3) / f"{m.group(4)}.mp3"
            if f.exists():
                return self.send(200, f.read_bytes(), "audio/mpeg")
        self.send(404, "not found", "text/plain")

    def do_POST(self):
        if self.path != "/notes":
            return self.send(404, "not found", "text/plain")
        n = int(self.headers.get("Content-Length", 0))
        notes = json.loads(self.rfile.read(n).decode("utf-8"))
        NOTES.parent.mkdir(parents=True, exist_ok=True)
        tmp = NOTES.with_suffix(".tmp"); tmp.write_text(json.dumps(notes, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(NOTES)
        self.send(200, "ok", "text/plain")


if __name__ == "__main__":
    DATA = build()
    print(f"{len(DATA)} clips on the review page -> http://127.0.0.1:8765/  (notes: {NOTES})", flush=True)
    ThreadingHTTPServer(("127.0.0.1", 8765), H).serve_forever()
