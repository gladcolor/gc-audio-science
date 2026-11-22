"""Writes <root>/_test/listen.html: a simple listening page.
  1) local test recordings (<root>/_test/*.wav and _test/bench/*.wav), the versions of each sentence side by side
  2) online lessons: pick a lesson, hear every clip from the audio repo, see Serena / old voice / no audio
Run again after new tests to refresh the list:  python make_listen.py"""
import html, json, re, sys, wave
from pathlib import Path

ONLY = re.compile(sys.argv[1]) if len(sys.argv) > 1 else None      # e.g. "^T" = only the sampling A/B versions
OUTNAME = sys.argv[2] if len(sys.argv) > 2 else "listen.html"
LABEL = {"T0.9-S0.9": "温度 0.9（现在的设置）", "T0.7-S0.7": "温度 0.7", "T0.5-S0.5": "温度 0.5",
         "T0.9-Sgreedy": "温度 0.9 + 子模型贪心",
         "T0.6-S0.6": "温度 0.6", "T0.55-S0.55": "温度 0.55"}

HERE = Path(__file__).resolve().parent
cfg = json.loads((HERE / "tts_config.json").read_text(encoding="utf-8"))
root = Path(cfg["root"]); test = root / "_test"

texts = {("en", "test"): "Diffusion moves molecules from high to low concentration, and it needs no energy.",
         ("zh", "test"): "长安是唐朝的都城，丝绸之路从这里出发。"}
for tj in test.glob("*.json"):                     # transcripts the bench used
    try:
        for c in json.loads(tj.read_text(encoding="utf-8"))["clips"]:
            texts[(c["lang"], c["key"])] = c["send"]
    except Exception:                              # noqa: BLE001
        pass


def dur(p):
    try:
        with wave.open(str(p)) as w:
            return round(w.getnframes() / w.getframerate(), 1)
    except Exception:                              # noqa: BLE001
        return None


rows = {}
for p in ([] if ONLY else sorted(test.glob("test_*.wav"))):
    lang = p.stem.split("_")[1]
    rows.setdefault((lang, "test"), []).append({"v": "test-voice", "src": p.name, "sec": dur(p)})
for p in sorted((test / "bench").glob("*.wav")):
    m = re.match(r"(.+?)_(en|zh)_([0-9a-f]{8})$", p.stem)
    if m and (not ONLY or ONLY.search(m.group(1))):
        v = LABEL.get(m.group(1)) or m.group(1).replace("single1", "单条").replace("batch", "批量")
        rows.setdefault((m.group(2), m.group(3)), []).append({"v": v, "src": "bench/" + p.name, "sec": dur(p)})
local = [{"lang": k[0], "key": k[1], "text": texts.get(k, ""), "files": v} for k, v in
         sorted(rows.items(), key=lambda kv: (kv[0][0], len(texts.get(kv[0], ""))))]

page = r"""<!doctype html>
<html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>朗读试听</title>
<style>
:root{--bg:#fafaf7;--fg:#1d1d1b;--muted:#6b6b66;--line:#e3e2dc;--card:#fff;--accent:#2f6f5e;--warn:#a35a00;--bad:#9b2c2c}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--fg:#ecebe6;--muted:#9a9993;--line:#2e2d2a;--card:#1f1f1d;--accent:#7cc4ad;--warn:#e0a458;--bad:#e58b8b}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 system-ui,"Segoe UI","Microsoft YaHei",sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px 64px}h1{font-size:22px;margin:0 0 4px}h2{font-size:17px;margin:32px 0 8px}
.sub{color:var(--muted);margin:0 0 8px}.row{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 12px;margin:8px 0}
.meta{color:var(--muted);font-size:12px}.text{margin:2px 0 6px}.vers{display:flex;flex-wrap:wrap;gap:10px}
.ver{display:flex;flex-direction:column;gap:2px;font-size:12px;color:var(--muted)}audio{height:32px;max-width:100%}
.tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:10px;border:1px solid currentColor;margin-left:6px}
.serena{color:var(--accent)}.old{color:var(--warn)}.none{color:var(--bad)}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:8px 0}select,input{font:inherit;padding:5px 8px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg);max-width:100%}
#lessonSel{min-width:0;flex:1 1 320px}.sum{color:var(--muted);font-size:13px}
</style></head><body><main>
<h1>朗读试听</h1><p class="sub">Qwen3-TTS · Serena · 本页由 <code>make_listen.py</code> 生成</p>

<h2>本机测试录音</h2>
<p class="sub">同一句话的不同版本放在一起：单条 = 一次一条；p1/p2… = 几个模型同时跑；批量N = 一次生成 N 句。</p>
<div id="local"></div>

<h2>线上课程（音频仓库）</h2>
<div class="bar"><select id="lessonSel"><option>加载课程列表…</option></select>
<select id="langSel"><option value="">两种语言</option><option value="en">English</option><option value="zh">中文</option></select>
<a id="pageLink" target="_blank" rel="noopener"></a></div>
<div class="sum" id="sum"></div><div id="clips"></div>
</main>
<script>
const LOCAL = __LOCAL__;
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
document.getElementById('local').innerHTML = LOCAL.length ? LOCAL.map(r =>
  `<div class="row"><div class="meta">${r.lang} · ${r.key} · ${r.text.length} 字符</div><div class="text">${esc(r.text)}</div>
   <div class="vers">${r.files.map(f => `<div class="ver"><span>${esc(f.v)}${f.sec ? ' · ' + f.sec + ' s' : ''}</span>
   <audio controls preload="none" src="${esc(f.src)}"></audio></div>`).join('')}</div></div>`).join('')
  : '<p class="sub">还没有测试录音。</p>';

const T = 'https://shanchuan.org/middle/readaloud/';
let IX = null;
const bust = () => 'v=' + Date.now();
fetch(T + 'index.json?' + bust()).then(r => r.json()).then(ix => {
  IX = ix; const sel = document.getElementById('lessonSel'); const groups = {};
  ix.lessons.forEach(l => (groups[l.id.split('/')[0]] ||= []).push(l));
  sel.innerHTML = '<option value="">选一课…</option>' + Object.entries(groups).map(([s, ls]) =>
    `<optgroup label="${esc(s)}">${ls.map(l => `<option value="${esc(l.id)}">${esc(l.zh)} · ${esc(l.en)}</option>`).join('')}</optgroup>`).join('')
    + `<optgroup label="_shared"><option value="_shared">共享句（地方书）</option></optgroup>`;
  const want = location.hash.slice(1); if (want) { sel.value = want; show(); }
}).catch(e => document.getElementById('sum').textContent = '课程列表加载失败：' + e);

function loadManifest(url) {
  return new Promise(res => {
    window.LabAudioManifest = m => res(m);
    const s = document.createElement('script'); s.src = url + '?' + bust();
    s.onerror = () => res(null); document.head.appendChild(s); setTimeout(() => res(null), 8000);
  });
}
async function show() {
  const id = document.getElementById('lessonSel').value, lang = document.getElementById('langSel').value;
  const out = document.getElementById('clips'), sum = document.getElementById('sum'), link = document.getElementById('pageLink');
  out.innerHTML = ''; sum.textContent = ''; link.textContent = ''; if (!id || !IX) return;
  location.hash = id;
  const e = id === '_shared' ? IX.shared : IX.lessons.find(l => l.id === id);
  const repo = IX.repos[e.repo];
  if (e.url) { link.href = e.url; link.textContent = '打开课程页面 ↗'; }
  sum.textContent = '加载中…';
  const [tr, man, led] = await Promise.all([
    fetch(T + (id === '_shared' ? 'shared' : id) + '.json?' + bust()).then(r => r.json()),
    loadManifest(repo + id + '/manifest.js'),
    fetch(repo + 'status/ledger.tsv?' + bust()).then(r => r.ok ? r.text() : '').catch(() => '')]);
  const serena = new Set(led.split('\n').slice(1).map(l => l.split('\t')).filter(p => p[2] === id).map(p => p[0] + ':' + p[1]));
  const has = { en: new Set(((man && man.en) || '').split(/\s+/)), zh: new Set(((man && man.zh) || '').split(/\s+/)) };
  const clips = tr.clips.filter(c => !lang || c.lang === lang);
  const n = { s: 0, o: 0, x: 0 };
  out.innerHTML = clips.map(c => {
    const rec = has[c.lang].has(c.key), sr = serena.has(c.lang + ':' + c.key);
    const tag = !rec ? '<span class="tag none">无录音（浏览器朗读）</span>' : sr ? '<span class="tag serena">Serena</span>' : '<span class="tag old">旧声音</span>';
    rec ? (sr ? n.s++ : n.o++) : n.x++;
    return `<div class="row"><div class="meta">${c.lang} · ${c.key} · ${c.send.length} 字符 ${tag}</div><div class="text">${esc(c.send)}</div>
      ${rec ? `<audio controls preload="none" src="${repo}${id}/${c.lang}/${c.key}.mp3"></audio>` : ''}</div>`;
  }).join('');
  sum.textContent = `${clips.length} 条：Serena ${n.s} · 旧声音 ${n.o} · 无录音 ${n.x}` + (man ? '' : '（这一课还没有 manifest）');
}
document.getElementById('lessonSel').onchange = show; document.getElementById('langSel').onchange = show;
</script></body></html>
"""
(test / OUTNAME).write_text(page.replace("__LOCAL__", json.dumps(local, ensure_ascii=False)), encoding="utf-8")
print(f"wrote {test / OUTNAME}: {len(local)} local sentences, {sum(len(r['files']) for r in local)} recordings")
