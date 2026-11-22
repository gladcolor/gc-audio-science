"""A/B test of the CustomVoice `instruct` (speaking-style instruction) on the clips the user judged "redo" in the
review (E:\\gc-audio\\_test\\qa\\review_shown.json + review_notes.json). Same settings as production (T 0.5 / 0.5).
  A  no instruction (a fresh retry: shows how much a plain re-roll helps)
  B  teaching style        C  recitation style (语文 only)
Writes MP3s (-16 LUFS, as published) to E:\\gc-audio\\_test\\instruct\\<setting>\\<key>.mp3, results.json and
listen.html (current published file vs A/B/C). Run only while the worker is idle (the GPU is free).
  python bench_instruct.py"""
import html, json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tts_worker as W                                   # noqa: E402

ROOT = Path("E:/gc-audio")
OUT = ROOT / "_test" / "instruct"
SETTINGS = [
    ("A", None),
    ("B", "用自然、清晰、有精神的讲解语气，语速适中。"),
    ("C", "用饱满、有感情的朗诵语气，语速适中，句子之间连贯。"),
]


def main():
    cfg = W.load_config(Path(__file__).resolve().parent / "tts_config.json")
    cfg["decode_one_by_one"] = True
    cfg["gpu_mem_fraction"] = 0.9                        # the worker is idle: this test may use the whole GPU
    qa = cfg["qa"]
    shown = json.loads((ROOT / "_test/qa/review_shown.json").read_text(encoding="utf-8"))
    notes = json.loads((ROOT / "_test/qa/review_notes.json").read_text(encoding="utf-8"))
    rows = [r for r in shown if r["lang"] == "zh" and
            (notes.get(r["id"], {}).get("verdict") == "redo" or notes.get(r["id"], {}).get("note"))
            and notes.get(r["id"], {}).get("verdict") != "keep"]
    print(f"{len(rows)} clips", flush=True)
    model = W.load_model(cfg)
    model.generate_custom_voice(text="预热。", language="Chinese", speaker=cfg["speaker"], max_new_tokens=60)
    from concurrent.futures import ProcessPoolExecutor
    pool = ProcessPoolExecutor(6)
    res = {r["id"]: {"row": r, "notes": notes.get(r["id"], {})} for r in rows}
    for name, instruct in SETTINGS:
        group = [r for r in rows if name != "C" or r["lesson"].startswith("yuwen/")]
        group.sort(key=lambda r: len(r["text"]))
        for i in range(0, len(group), 32):
            part = group[i:i + 32]
            texts = [r["text"] for r in part]
            slow = any(r["lesson"].startswith("yuwen/") for r in part)
            t = time.time()
            kw = dict(text=texts, language=["Chinese"] * len(texts), speaker=[cfg["speaker"]] * len(texts),
                      max_new_tokens=W.batch_tokens(texts, "zh", slow), **W.gen_kwargs(cfg))
            if instruct:
                kw["instruct"] = [instruct] * len(texts)
            wavs, sr = model.generate_custom_voice(**kw)
            print(f"{name} batch {i // 32 + 1}: {len(part)} clips in {time.time() - t:.0f}s", flush=True)
            futs = []
            for r, a in zip(part, wavs):
                pcm = W.pcm16(a)
                dst = OUT / name / f"{r['key']}.mp3"
                W.to_mp3(cfg, pcm, sr, dst)
                futs.append((r, pool.submit(W.check_clip_qa, pcm, sr, r["text"], "zh", qa, cfg["ffmpeg"])))
            for r, f in futs:
                q = f.result()
                res[r["id"]][name] = {"pace": round(q.pace or 0, 2), "f0": round(q.f0 or 0, 1),
                                      "ok": not q.reasons, "reasons": list(q.reasons)}
    (OUT / "results.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for name, _ in SETTINGS:
        got = [v[name] for v in res.values() if name in v]
        ok = sum(g["ok"] for g in got)
        paces = sorted(g["pace"] for g in got); f0s = sorted(g["f0"] for g in got)
        print(f"RESULT {name}: {ok}/{len(got)} pass the gate; pace median {paces[len(paces) // 2]:.2f}; "
              f"F0 median {f0s[len(f0s) // 2]:.0f}; F0 > 300: {sum(f > 300 for f in f0s)}", flush=True)
    write_page(res)


def write_page(res):
    def cell(v, name, key):
        if name not in v:
            return "<td></td>"
        m = v[name]
        mark = "" if m["ok"] else " class=bad"
        return (f'<td{mark}><audio controls preload="none" src="{name}/{key}.mp3"></audio>'
                f'<div class=m>{m["pace"]:.1f} 字/秒 · {m["f0"]:.0f} Hz</div></td>')
    trs = []
    for v in sorted(res.values(), key=lambda v: (v["row"]["lesson"], v["row"]["key"])):
        r = v["row"]; n = v["notes"]
        cur = f'../../{r["repo"]}/{r["lesson"]}/zh/{r["key"]}.mp3'
        tags = "、".join(n.get("tags") or []) + (" " + n["note"] if n.get("note") else "")
        trs.append(f'<tr><td class=t><div class=m>{html.escape(r["lesson"])} · {r["key"]} · 你的标签：{html.escape(tags)}</div>'
                   f'{html.escape(r["text"])}</td>'
                   f'<td><audio controls preload="none" src="{cur}"></audio><div class=m>{float(r["pace"]):.1f} 字/秒 · '
                   f'{float(r["f0"]):.0f} Hz</div></td>' + "".join(cell(v, s, r["key"]) for s, _ in SETTINGS) + "</tr>")
    page = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>语气指令对比</title><style>
:root{{--bg:#fafaf7;--fg:#1d1d1b;--muted:#6b6b66;--line:#e3e2dc;--bad:#9b2c2c}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161615;--fg:#ecebe6;--muted:#9a9993;--line:#2e2d2a;--bad:#e58b8b}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,"Microsoft YaHei",sans-serif}}
main{{padding:16px}}table{{border-collapse:collapse;width:100%}}td,th{{border-bottom:1px solid var(--line);padding:6px;vertical-align:top}}
th{{text-align:left;position:sticky;top:0;background:var(--bg)}}td.t{{max-width:340px}}.m{{color:var(--muted);font-size:12px}}
audio{{height:30px;width:200px}}td.bad .m{{color:var(--bad)}}
</style></head><body><main><h1 style="font-size:19px">语气指令对比</h1>
<p class=m>现有 = 网站上的录音（试了 5 次后的最好一次）。A = 不加指令重录一次。B = 讲解语气：{html.escape(SETTINGS[1][1])}
C = 朗诵语气（只录语文）：{html.escape(SETTINGS[2][1])} 红色数字 = 没通过质检（音高 185–300 Hz，语速 3.5–6.5 字/秒）。</p>
<table><tr><th>文字</th><th>现有</th><th>A 不加指令</th><th>B 讲解语气</th><th>C 朗诵语气</th></tr>{"".join(trs)}</table></main></body></html>"""
    (OUT / "listen.html").write_text(page, encoding="utf-8")
    print(f"page: {OUT / 'listen.html'}", flush=True)


if __name__ == "__main__":
    main()
