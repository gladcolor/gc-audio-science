"""Test: can the model itself make longer pauses at sentence ends?  Same texts, several model-side variants
(text layout, instruction, talker temperature), 2 tries each. Measures the pause at 。！？ and at ，、；： (silence
matched to the punctuation, see pause_fix.py), pitch and pace. Writes E:\\gc-audio\\_test\\pause\\<v>_<n>_<try>.mp3,
results.json and listen.html. Run only while the worker is idle.
  python bench_pause.py"""
import html, json, sys, time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench_whole as BW                                 # noqa: E402
import pause_fix as PF                                   # noqa: E402
import tts_worker as W                                   # noqa: E402

OUT = Path("E:/gc-audio/_test/pause")
TRIES = 2
TEACH = "用自然、清晰、有精神的讲解语气，语速适中。"
PAUSE = "句与句之间要有明显的停顿，句号处的停顿比逗号长，语速适中，像老师给学生朗读。"
nl = lambda s: s.replace("。", "。\n").replace("？", "？\n").replace("！", "！\n")
nl2 = lambda s: s.replace("。", "。\n\n").replace("？", "？\n\n").replace("！", "！\n\n")
RECITE = "用朗诵的语气，句与句之间停顿分明，语速适中。"
lines = lambda it, body: it["title"] + "\n" + it["author"] + "\n\n" + body   # title and author on their own lines
VARIANTS = [   # (id, label, input text from the item, instruction, talker temperature)
    ("V0", "现在的做法", lambda it: it["send"], None, None),
    ("V1", "句号后换行", lambda it: nl(it["send"]), None, None),
    ("V2", "句号后空一行", lambda it: nl2(it["send"]), None, None),
    ("V3", "停顿指令", lambda it: it["send"], PAUSE, None),
    ("V4", "讲解语气 + 句号后换行", lambda it: nl(it["send"]), TEACH, None),
    ("V5", "温度 0.65", lambda it: it["send"], None, 0.65),
    ("V6", "朗诵语气，停顿分明", lambda it: it["send"], RECITE, None),
    ("V7", "朗诵语气 + 句号后换行", lambda it: nl(it["send"]), RECITE, None),
    ("V8", "朗诵语气 + 题目作者单独成行 + 句号后换行", lambda it: lines(it, nl(it["body"])), RECITE, None),
    ("V9", "停顿指令 + 句号后换行", lambda it: nl(it["send"]), PAUSE, None),
    ("V10", "题目作者单独成行", lambda it: lines(it, it["body"]), None, None),
    ("V11", "朗诵语气 + 题目作者单独成行", lambda it: lines(it, it["body"]), RECITE, None),
]


def texts():
    clips = BW.site_clips(); by = {c["key"]: c for c in clips}
    poems = {t: (a, b) for t, a, b in BW.POEMS}
    out = [("春望", "杜甫", poems["春望"][1]), ("钱塘湖春行", "白居易", poems["钱塘湖春行"][1]),
           ("水调歌头", "苏轼", poems["水调歌头"][1]),
           ("桃花源记（前两段）", "陶渊明", by["c399a1a1"]["send"] + by["f682d512"]["send"])]
    return [dict(n=i, title=t, author=a, body=b, send=f"{t}。{a}。{b}") for i, (t, a, b) in enumerate(out)]


def main():
    cfg = W.load_config(Path(__file__).resolve().parent / "tts_config.json")
    cfg["decode_one_by_one"] = True; cfg["gpu_mem_fraction"] = 0.9
    PF.FFMPEG = cfg["ffmpeg"]
    qa = dict(cfg["qa"], pace=dict(cfg["qa"]["pace"], zh=[3.0, 6.5]))
    its = texts()
    OUT.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:])                             # run only these variants; earlier results are kept
    rfile = OUT / "results.json"
    res = json.loads(rfile.read_text(encoding="utf-8"))["results"] if (only and rfile.exists()) else {}
    model = W.load_model(cfg)
    model.generate_custom_voice(text="预热。", language="Chinese", speaker=cfg["speaker"], max_new_tokens=60)
    for vid, label, tf, ins, temp in VARIANTS:
        if only and vid not in only:
            continue
        jobs = [(it, t) for it in its for t in range(TRIES)]
        sends = [tf(it) for it, _ in jobs]
        kw = dict(W.gen_kwargs(cfg))
        if temp is not None:
            kw["temperature"] = temp
        if ins:
            kw["instruct"] = [ins] * len(sends)
        t = time.time()
        wavs, sr = model.generate_custom_voice(text=sends, language=["Chinese"] * len(sends),
                                               speaker=[cfg["speaker"]] * len(sends),
                                               max_new_tokens=W.batch_tokens(sends, "zh", True), **kw)
        print(f"{vid} {label}: {len(sends)} clips in {time.time() - t:.0f}s", flush=True)
        for (it, tr), a in zip(jobs, wavs):
            pcm = W.pcm16(a)
            f = OUT / f"{vid}_{it['n']}_{tr + 1}.mp3"
            W.to_mp3(cfg, pcm, sr, f)
            x = np.frombuffer(pcm, dtype="<i2").astype("float32") / 32768
            q = W.check_clip_qa(pcm, sr, it["send"], "zh", qa, cfg["ffmpeg"])
            res[f"{vid}_{it['n']}_{tr + 1}"] = dict(v=vid, n=it["n"], tr=tr + 1, sec=round(len(x) / sr, 1),
                                                    pace=round(q.pace or 0, 2), f0=round(q.f0 or 0), ok=not q.reasons)
    by_n = {it["n"]: it for it in its}
    for name, r in res.items():                          # pause measures for every clip (old ones too), same method
        x = PF.decode(OUT / f"{name}.mp3", cfg["ffmpeg"])
        r.update(pause_metrics(by_n[r["n"]]["send"], x))
    (OUT / "results.json").write_text(json.dumps(dict(texts=its, results=res), ensure_ascii=False, indent=1), encoding="utf-8")
    for vid, label, *_ in VARIANTS:
        rs = [r for r in res.values() if r["v"] == vid]
        if not rs:
            continue
        print(f"RESULT {vid} {label:14s} after title {np.median([r['title_p'] for r in rs]):.2f}s, "
              f"after author {np.median([r['author_p'] for r in rs]):.2f}s, pause at 。 median {np.median([r['major_med'] for r in rs]):.2f}s, "
              f"at ， {np.median([r['minor_med'] for r in rs]):.2f}s, sentence ends >= 0.8 s: "
              f"{np.mean([r['major_08'] for r in rs]) * 100:.0f}%, pace {np.median([r['pace'] for r in rs]):.2f}, "
              f"F0 {np.median([r['f0'] for r in rs]):.0f}, runaway {sum(r['pace'] < 2.0 for r in rs)}/{len(rs)}", flush=True)
    write_page(its, res)


def pause_metrics(send, x):
    """pauses after the title, after the author, median at 。！？ and at ，、；：, share of sentence ends >= 0.8 s
    (the user: a pause at 。 should be at least about 0.8 s)"""
    sil, t0, t1 = PF.silences(x); mk, total = PF.marks(send)
    sil, pairs = PF.match(sil, mk, total, t0, t1)
    at = {j: sil[i][1] - sil[i][0] for i, j in pairs.items()}           # pause after mark j
    body = [(j, k) for j, (_, k) in enumerate(mk) if j >= 2 and j < len(mk) - 1]   # poem text, not the last mark
    maj = [at[j] for j, k in body if k == "major" and j in at]
    mnr = [at[j] for j, k in body if k == "minor" and j in at]
    n_major = sum(1 for _, k in body if k == "major")
    r2 = lambda v: round(float(v), 2)
    return dict(title_p=r2(at.get(0, 0)), author_p=r2(at.get(1, 0)),
                major_med=r2(np.median(maj)) if maj else 0.0, minor_med=r2(np.median(mnr)) if mnr else 0.0,
                major_08=r2(sum(1 for d in maj if d >= 0.8) / max(1, n_major)))


def write_page(its, res):
    secs = []
    for it in its:
        rows = []
        for vid, label, *_ in VARIANTS:
            cells = []
            for tr in range(1, TRIES + 1):
                r = res.get(f"{vid}_{it['n']}_{tr}")
                if not r:
                    continue
                cells.append(f'<div><audio controls preload="none" src="{vid}_{it["n"]}_{tr}.mp3"></audio>'
                             f'<div class="m{"" if r["ok"] else " bad"}">题目后 {r.get("title_p", 0):.2f} 秒 · 作者后 '
                             f'{r.get("author_p", 0):.2f} 秒 · 句号处停 {r["major_med"]:.2f} 秒（停够 0.8 秒的 '
                             f'{r.get("major_08", 0) * 100:.0f}%）· 逗号处 {r["minor_med"]:.2f} 秒 · {r["pace"]:.1f} 字/秒'
                             f'{" · 中途停读" if r["pace"] < 2.0 else ""}</div></div>')
            rows.append(f'<tr><td class=l>{html.escape(label)}</td><td><div class=pair>{"".join(cells)}</div></td></tr>')
        secs.append(f'<section><h2>{html.escape(it["title"])} · {html.escape(it["author"])}</h2>'
                    f'<p class=t>{html.escape(it["body"])}</p><table>{"".join(rows)}</table></section>')
    page = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>句末停顿测试</title><style>
:root{{--bg:#fafaf7;--fg:#1d1d1b;--muted:#6b6b66;--line:#e3e2dc;--bad:#9b2c2c}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161615;--fg:#ecebe6;--muted:#9a9993;--line:#2e2d2a;--bad:#e58b8b}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 system-ui,"Microsoft YaHei",sans-serif}}
main{{max-width:1000px;margin:0 auto;padding:16px}}h1{{font-size:20px}}h2{{font-size:16px;margin:0 0 4px}}
section{{border-top:1px solid var(--line);padding:14px 0}}.t{{margin:4px 0 10px}}.m{{color:var(--muted);font-size:12px}}
.bad{{color:var(--bad)}}table{{border-collapse:collapse;width:100%}}td{{border-bottom:1px solid var(--line);padding:6px;vertical-align:top}}
td.l{{width:170px;font-size:14px}}.pair{{display:flex;flex-wrap:wrap;gap:12px}}audio{{height:30px;width:260px}}
</style></head><body><main><h1>句末停顿测试</h1>
<p class=m>同样的文字，用不同的办法让模型自己在句号处停得更久，每种录 2 次。数字是测出的停顿：
题目后、作者后，以及诗文中句号处和逗号处停顿的中位数。目标：题目后、作者后和句号处至少约 0.8 秒，逗号处短一些。</p>{"".join(secs)}</main></body></html>"""
    (OUT / "listen.html").write_text(page, encoding="utf-8")
    print(f"page: {OUT / 'listen.html'}", flush=True)


if __name__ == "__main__":
    main()
