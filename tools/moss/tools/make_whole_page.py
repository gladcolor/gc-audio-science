"""Listening page for the whole-text test while it is still running: every clip already written to
E:\\gc-audio\\_test\\whole\\ appears with its length and pace. bench_whole.py overwrites the page with the full
measurements when it ends.  python make_whole_page.py [--loop]  (--loop: rewrite every 60 s until results.json exists)"""
import html, json, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench_whole as BW                                 # noqa: E402
import tts_worker as W                                   # noqa: E402

OUT = BW.OUT
LABEL = {"A": "不加指令", "B": "讲解语气"}


def items():
    clips = BW.site_clips(); by_key = {c["key"]: c for c in clips}
    out = []
    for title, author, text in BW.POEMS:
        out.append(dict(title=title, author=author, body=text, lines=BW.line_cover(text, clips)[0]))
    for title, author, keys in BW.PROSE:
        out.append(dict(title=title, author=author, body="".join(by_key[k]["send"] for k in keys),
                        lines=[by_key[k] for k in keys]))
    for i, it in enumerate(out):
        it["n"] = i; it["send"] = f"{it['title']}。{it['author']}。{it['body']}"
    return out


def dur(ffprobe, f):
    r = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(f)],
                       capture_output=True, text=True, timeout=60)
    return float(r.stdout)


def write(its, ffprobe):
    rows, n_done = [], 0
    for it in its:
        srcs = [f"../../gc-audio-lang-math/yuwen/{c['lesson']}/zh/{c['key']}.mp3" for c in it["lines"]
                if (BW.ROOT / "gc-audio-lang-math" / "yuwen" / c["lesson"] / "zh" / f"{c['key']}.mp3").exists()]
        seq = (f'<button type=button data-seq=\'{json.dumps(srcs)}\'>▶ 逐句连播（{len(srcs)} 段）</button>'
               if srcs else '<span class=m>网站上没有这首的逐句录音</span>')
        tries = []
        for k in ("A1", "A2", "B1", "B2"):
            f = OUT / f"{it['n']:02d}_{k}.mp3"
            if f.exists() and time.time() - f.stat().st_mtime > 5:
                d = dur(ffprobe, f); n_done += 1
                tries.append(f'<div class=try><span class=m>{LABEL[k[0]]} {k[1]}</span> '
                             f'<audio controls preload="none" src="{f.name}?v={int(f.stat().st_mtime)}"></audio>'
                             f'<div class=m>{d:.0f} 秒 · {W.speech_len(it["send"], "zh") / d:.1f} 字/秒</div></div>')
            else:
                tries.append(f'<div class="try m">{LABEL[k[0]]} {k[1]}：还没录到</div>')
        rows.append(f'<section><h2>{html.escape(it["title"])} · {html.escape(it["author"])} '
                    f'<span class=m>{len(it["send"])} 字</span></h2><p class=t>{html.escape(it["body"])}</p>'
                    f'<div class=cmp><div><div class=h>现在：逐句录音</div>{seq}</div>'
                    f'<div><div class=h>整篇一次录</div>{"".join(tries)}</div></div></section>')
    page = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>整篇朗读测试</title><style>
:root{{--bg:#fafaf7;--fg:#1d1d1b;--muted:#6b6b66;--line:#e3e2dc;--acc:#2f6f5e}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161615;--fg:#ecebe6;--muted:#9a9993;--line:#2e2d2a;--acc:#7cc4ad}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 system-ui,"Microsoft YaHei",sans-serif}}
main{{max-width:1000px;margin:0 auto;padding:16px}}h1{{font-size:20px}}h2{{font-size:16px;margin:0 0 4px}}
section{{border-top:1px solid var(--line);padding:14px 0}}.t{{margin:4px 0 10px}}.m{{color:var(--muted);font-size:12px}}
.h{{font-size:13px;color:var(--muted);margin-bottom:4px}}.cmp{{display:grid;grid-template-columns:1fr 2fr;gap:16px}}
@media (max-width:700px){{.cmp{{grid-template-columns:1fr}}}}audio{{height:30px;width:100%;max-width:360px}}.try{{margin-bottom:6px}}
button{{font:inherit;padding:4px 12px;border-radius:14px;border:1px solid var(--acc);background:var(--bg);color:var(--acc);cursor:pointer}}
</style></head><body><main><h1>整篇朗读测试（录音中）</h1>
<p class=m>已录好 {n_done} 条，共 {len(its) * 4} 条，更新于 {time.strftime('%H:%M')}。刷新页面可看到新录好的。左边：网站现在的逐句录音按顺序连播。
右边：同样的文字加上题目、作者一次录完：不加指令 2 次，加“讲解语气”指令 2 次。音高等指标在测试结束后补上。</p>
{"".join(rows)}</main><script>
let cur = null;
document.addEventListener('click', e => {{ const b = e.target.closest('button[data-seq]'); if (!b) return;
  if (cur) {{ cur.pause(); cur = null; }}
  const list = JSON.parse(b.dataset.seq); let i = 0;
  const next = () => {{ if (i >= list.length) return; cur = new Audio(list[i++]); cur.onended = next; cur.play(); }};
  document.querySelectorAll('audio').forEach(a => a.pause()); next(); }});
document.addEventListener('play', e => {{ if (cur && e.target !== cur) {{ cur.pause(); cur = null; }} }}, true);
</script></body></html>"""
    (OUT / "listen.html").write_text(page, encoding="utf-8")
    return n_done


if __name__ == "__main__":
    cfg = W.load_config(Path(__file__).resolve().parent / "tts_config.json")
    ffprobe = str(Path(cfg["ffmpeg"]).with_name("ffprobe.exe"))
    its = items()
    start = time.time()
    while True:
        if (OUT / "results.json").exists() and (OUT / "results.json").stat().st_mtime > start:
            break                                        # bench_whole.py has written the final page
        print(f"{time.strftime('%H:%M')} page: {write(its, ffprobe)} clips", flush=True)
        if "--loop" not in sys.argv:
            break
        time.sleep(60)
