"""Test: voice cloning with the Qwen3-TTS Base model. A reference recording of Serena with clear pauses at sentence
ends is given as the voice prompt (ICL mode: reference audio + its text); the model should take over its rhythm.
References are picked automatically from the whole-text test (Serena preset recordings of other poems): pace
2.3-2.9 characters/s and the longest pauses at 。 compared with ，. Same 4 texts as the pause test (bench_pause.py),
2 tries per reference, production sampling (T 0.5 / 0.5). Writes E:\\gc-audio\\_test\\clone\\..., results.json and
listen.html (the preset Serena of the pause test next to the cloned versions). Run only while the GPU is free.
  python bench_clone.py"""
import html, json, shutil, sys, time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench_pause as BP                                 # noqa: E402
import pause_fix as PF                                   # noqa: E402
import tts_worker as W                                   # noqa: E402

OUT = Path("E:/gc-audio/_test/clone")
BASE = "E:/gc-audio/models/Qwen3-TTS-12Hz-1.7B-Base"
WHOLE = Path("E:/gc-audio/_test/whole")
TRIES = 2


def pick_refs(cfg, n=2):
    items = json.loads((WHOLE / "results.json").read_text(encoding="utf-8"))
    test_titles = {"春望", "钱塘湖春行", "水调歌头"}
    cands = []
    for it in items:
        if it["title"] in test_titles or len(it["send"]) > 80:
            continue
        for k, v in it["tries"].items():
            if not (2.3 <= v["pace"] <= 2.9) or v["capped"]:
                continue
            x = PF.decode(WHOLE / f"{it['n']:02d}_{k}.mp3", cfg["ffmpeg"])
            _, st = PF.apply(it["send"], x, 0.0, 0.0)
            if not st["major"]:
                continue
            maj, mnr = float(np.median(st["major"])), float(np.median(st["minor"])) if st["minor"] else 0.0
            cands.append(dict(title=it["title"], k=k, send=it["send"], file=WHOLE / f"{it['n']:02d}_{k}.mp3",
                              sec=v["sec"], pace=v["pace"], major=round(maj, 2), minor=round(mnr, 2),
                              score=maj - mnr + 0.5 * min(st["major"])))
    cands.sort(key=lambda c: -c["score"])
    out, seen = [], set()
    for c in cands:                                      # two different poems
        if c["title"] not in seen:
            out.append(c); seen.add(c["title"])
        if len(out) == n:
            break
    return out


def main():
    cfg = W.load_config(Path(__file__).resolve().parent / "tts_config.json")
    cfg["decode_one_by_one"] = True; cfg["gpu_mem_fraction"] = 0.9; cfg["model"] = BASE
    PF.FFMPEG = cfg["ffmpeg"]
    qa = dict(cfg["qa"], pace=dict(cfg["qa"]["pace"], zh=[2.2, 3.0]))
    OUT.mkdir(parents=True, exist_ok=True)
    refs = pick_refs(cfg)
    its = BP.texts()
    rec = BP.OUT / "V6_0_1.mp3"                          # 春望 read with the recitation instruction: 0.8-0.9 s at 。
    if rec.exists():
        m = BP.pause_metrics(its[0]["send"], PF.decode(rec, cfg["ffmpeg"]))
        sec = len(PF.decode(rec, cfg["ffmpeg"])) / PF.SR
        refs.append(dict(title="春望（朗诵语气，也是下面的测试文字之一）", k="V6#1", send=its[0]["send"], file=rec,
                         sec=round(sec, 1), pace=round(W.speech_len(its[0]["send"], "zh") / sec, 2),
                         major=m["major_med"], minor=m["minor_med"], score=0))
    for i, r in enumerate(refs):
        shutil.copy(r["file"], OUT / f"ref{i + 1}.mp3")
        print(f"reference {i + 1}: {r['title']} {r['k']} {r['sec']}s {r['pace']} c/s, pause at 。 {r['major']}s, "
              f"at ， {r['minor']}s", flush=True)
    model = W.load_model(cfg)
    res = {}
    for i, r in enumerate(refs):
        x = PF.decode(r["file"], cfg["ffmpeg"])
        prompt = model.create_voice_clone_prompt(ref_audio=(x, PF.SR), ref_text=r["send"])
        jobs = [(it, t) for it in its for t in range(TRIES)]
        sends = [it["send"] for it, _ in jobs]
        t = time.time()
        wavs, sr = model.generate_voice_clone(text=sends, language=["Chinese"] * len(sends),
                                              voice_clone_prompt=prompt * len(sends),
                                              max_new_tokens=W.batch_tokens(sends, "zh", True), **W.gen_kwargs(cfg))
        print(f"reference {i + 1}: {len(sends)} clips in {time.time() - t:.0f}s", flush=True)
        for (it, tr), a in zip(jobs, wavs):
            pcm = W.pcm16(a)
            name = f"R{i + 1}_{it['n']}_{tr + 1}"
            W.to_mp3(cfg, pcm, sr, OUT / f"{name}.mp3")
            y = np.frombuffer(pcm, dtype="<i2").astype("float32") / 32768
            q = W.check_clip_qa(pcm, sr, it["send"], "zh", qa, cfg["ffmpeg"])
            res[name] = dict(r=i + 1, n=it["n"], tr=tr + 1, sec=round(len(y) / sr, 1), pace=round(q.pace or 0, 2),
                             f0=round(q.f0 or 0), ok=not q.reasons, **BP.pause_metrics(it["send"], y))
    refs_out = [{k: (str(v) if isinstance(v, Path) else v) for k, v in r.items()} for r in refs]
    (OUT / "results.json").write_text(json.dumps(dict(refs=refs_out, results=res), ensure_ascii=False, indent=1),
                                      encoding="utf-8")
    for i in range(len(refs)):
        rs = [v for v in res.values() if v["r"] == i + 1]
        print(f"RESULT R{i + 1}: after title {np.median([v['title_p'] for v in rs]):.2f}s, after author "
              f"{np.median([v['author_p'] for v in rs]):.2f}s, pause at 。 median {np.median([v['major_med'] for v in rs]):.2f}s, at ， "
              f"{np.median([v['minor_med'] for v in rs]):.2f}s, sentence ends >= 0.8 s "
              f"{np.mean([v['major_08'] for v in rs]) * 100:.0f}%, pace {np.median([v['pace'] for v in rs]):.2f}, "
              f"F0 {np.median([v['f0'] for v in rs]):.0f}, runaway {sum(v['pace'] < 2.0 for v in rs)}/{len(rs)}",
              flush=True)
    write_page(its, refs, res)


def write_page(its, refs, res):
    base = json.loads((BP.OUT / "results.json").read_text(encoding="utf-8"))["results"]

    def cell(src, r):
        return (f'<div><audio controls preload="none" src="{src}"></audio><div class=m>题目后 {r.get("title_p", 0):.2f} 秒 · '
                f'作者后 {r.get("author_p", 0):.2f} 秒 · 句号处停 {r["major_med"]:.2f} 秒（停够 0.8 秒的 '
                f'{r.get("major_08", 0) * 100:.0f}%）· 逗号处 {r["minor_med"]:.2f} 秒 · {r["pace"]:.1f} 字/秒'
                f'{" · 中途停读" if r["pace"] < 2.0 else ""}</div></div>')
    head = "".join(f'<div><b>参考录音 {i + 1}</b>：{html.escape(r["title"])}（{r["sec"]:.0f} 秒，{r["pace"]:.1f} 字/秒，'
                   f'句号处停 {r["major"]:.2f} 秒，逗号处 {r["minor"]:.2f} 秒）<br><audio controls preload="none" '
                   f'src="ref{i + 1}.mp3"></audio></div>' for i, r in enumerate(refs))
    secs = []
    for it in its:
        rows = [f'<tr><td class=l>现在的 Serena</td><td><div class=pair>' + "".join(
            cell(f"../pause/V0_{it['n']}_{t}.mp3", base[f"V0_{it['n']}_{t}"]) for t in (1, 2)
            if f"V0_{it['n']}_{t}" in base) + "</div></td></tr>"]
        for i in range(len(refs)):
            rows.append(f'<tr><td class=l>克隆：参考录音 {i + 1}</td><td><div class=pair>' + "".join(
                cell(f"R{i + 1}_{it['n']}_{t}.mp3", res[f"R{i + 1}_{it['n']}_{t}"]) for t in (1, 2)
                if f"R{i + 1}_{it['n']}_{t}" in res) + "</div></td></tr>")
        secs.append(f'<section><h2>{html.escape(it["title"])} · {html.escape(it["author"])}</h2>'
                    f'<p class=t>{html.escape(it["body"])}</p><table>{"".join(rows)}</table></section>')
    page = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>声音克隆测试</title><style>
:root{{--bg:#fafaf7;--fg:#1d1d1b;--muted:#6b6b66;--line:#e3e2dc}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161615;--fg:#ecebe6;--muted:#9a9993;--line:#2e2d2a}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 system-ui,"Microsoft YaHei",sans-serif}}
main{{max-width:1000px;margin:0 auto;padding:16px}}h1{{font-size:20px}}h2{{font-size:16px;margin:0 0 4px}}
section{{border-top:1px solid var(--line);padding:14px 0}}.t{{margin:4px 0 10px}}.m{{color:var(--muted);font-size:12px}}
table{{border-collapse:collapse;width:100%}}td{{border-bottom:1px solid var(--line);padding:6px;vertical-align:top}}
td.l{{width:150px;font-size:14px}}.pair{{display:flex;flex-wrap:wrap;gap:12px}}audio{{height:30px;width:260px}}
.refs{{display:grid;gap:10px;margin:10px 0 16px}}
</style></head><body><main><h1>声音克隆测试</h1>
<p class=m>Base 模型以一段 Serena 的录音为参考，模仿它的声音和节奏。参考录音选自整篇测试中节奏最好的两首诗（不在下面的测试文字里）。
每种录 2 次，设置和正式录音相同。先听音色是否还是 Serena，再听句号处的停顿。</p>
<div class=refs>{head}</div>{"".join(secs)}</main></body></html>"""
    (OUT / "listen.html").write_text(page, encoding="utf-8")
    print(f"page: {OUT / 'listen.html'}", flush=True)


if __name__ == "__main__":
    main()
