"""Listening page to choose the pause at sentence ends for explanatory clips: a few published Chinese clips from
different subjects, each as published and with every pause at 。！？ lengthened to at least 0.6 s and 0.8 s (only
for deciding the target; not used for publishing). Writes E:\\gc-audio\\_test\\calib\\.  python make_calib.py"""
import html, json, random, urllib.request
from pathlib import Path

import pause_fix as PF
import tts_worker as W

OUT = Path("E:/gc-audio/_test/calib")
LEVELS = (0.6, 0.8)


def main():
    cfg = W.load_config(Path(__file__).resolve().parent / "tts_config.json"); PF.FFMPEG = cfg["ffmpeg"]
    OUT.mkdir(parents=True, exist_ok=True)
    idx = json.loads(urllib.request.urlopen("https://shanchuan.org/middle/readaloud/index.json", timeout=60).read())
    random.seed(7)
    rows, subjects = [], set()
    lessons = [l for l in idx["lessons"] if not l["id"].startswith("yuwen/")]
    random.shuffle(lessons)
    for l in lessons:
        subj = l["id"].split("/")[0]
        if subj in subjects:
            continue
        t = json.loads(urllib.request.urlopen(f"https://shanchuan.org/middle/readaloud/{l['id']}.json", timeout=60).read())
        clips = [c for c in t["clips"] if c["lang"] == "zh" and 70 <= len(c["send"]) <= 150
                 and sum(c["send"].count(p) for p in "。！？") >= 3]
        clips = [c for c in clips if (Path("E:/gc-audio") / l["repo"] / l["id"] / "zh" / f"{c['key']}.mp3").exists()]
        if not clips:
            continue
        c = clips[0]; subjects.add(subj)
        src = Path("E:/gc-audio") / l["repo"] / l["id"] / "zh" / f"{c['key']}.mp3"
        x = PF.decode(src)
        files = {"现在": f"../../{l['repo']}/{l['id']}/zh/{c['key']}.mp3"}
        for lv in LEVELS:
            y, _ = PF.apply(c["send"], x, lv, 0.0)
            name = f"{len(rows)}_{int(lv * 10)}.mp3"; PF.encode(y, OUT / name); files[f"句号处至少 {lv} 秒"] = name
        rows.append((l, c, files))
        if len(rows) == 6:
            break
    secs = "".join(
        f'<section><h2>{html.escape(l["zh"])} <span class=m>{html.escape(l["id"])}</span></h2><p class=t>{html.escape(c["send"])}</p>'
        + "".join(f'<div class=row><span class=l>{k}</span><audio controls preload="none" src="{v}"></audio></div>'
                  for k, v in files.items()) + "</section>" for l, c, files in rows)
    page = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>讲解句末停顿</title><style>
:root{{--bg:#fafaf7;--fg:#1d1d1b;--muted:#6b6b66;--line:#e3e2dc}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161615;--fg:#ecebe6;--muted:#9a9993;--line:#2e2d2a}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 system-ui,"Microsoft YaHei",sans-serif}}
main{{max-width:900px;margin:0 auto;padding:16px}}h1{{font-size:20px}}h2{{font-size:16px;margin:0 0 4px}}
section{{border-top:1px solid var(--line);padding:14px 0}}.t{{margin:4px 0 10px}}.m{{color:var(--muted);font-size:12px}}
.row{{display:flex;align-items:center;gap:12px;margin:4px 0}}.l{{width:130px;font-size:14px}}audio{{height:30px;width:100%;max-width:420px}}
</style></head><body><main><h1>讲解录音：句号处停多久合适</h1>
<p class=m>每条讲解录音三个版本：现在网站上的；把每个句号、问号、叹号处的停顿补到至少 0.6 秒；补到至少 0.8 秒。
声音和读法完全相同，只有句末停顿不同。这些版本只用来决定标准，不会发布。</p>{secs}</main></body></html>"""
    (OUT / "listen.html").write_text(page, encoding="utf-8")
    print(f"{len(rows)} clips -> {OUT / 'listen.html'}")


if __name__ == "__main__":
    main()
