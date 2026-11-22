"""MOSS-TTS round 2: explanatory Chinese and English, voice cloned from Serena explanatory recordings (one Chinese,
one English reference, picked from the published clips), with pause tags after sentence ends ([pause 0.6s] vs
[pause 0.8s]) and without. The published Qwen3-TTS clip of the same text is shown for comparison.
Runs in E:\\gc-audio\\venv-moss. Writes E:\\gc-audio\\_test\\moss2\\..., results.json, listen.html.
  E:\\gc-audio\\venv-moss\\Scripts\\python.exe bench_moss2.py"""
import html, json, random, re, subprocess, sys, time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pause_fix as PF                                   # noqa: E402
import tts_worker as W                                   # noqa: E402

ROOT = Path("E:/gc-audio")
OUT = ROOT / "_test" / "moss2"
MODEL = ROOT / "models" / "MOSS-TTS-Local-Transformer-v1.5"
CODEC = ROOT / "models" / "MOSS-Audio-Tokenizer-v2"
TRS = ROOT / "_test" / "textscan" / "transcripts"
TRIES = 2
GEN = dict(max_new_tokens=4096, do_sample=True, audio_temperature=1.7, audio_top_p=0.8, audio_top_k=25,
           audio_repetition_penalty=1.0)


def with_pauses(s, sec, lang):
    ends = "。！？" if lang == "zh" else ".!?"
    pat = rf"([{re.escape(ends)}])(?=\s*\S)" if lang == "zh" else r"((?<!\d)[.!?])(?=\s+[A-Z\"“(])"
    return re.sub(pat, lambda m: m.group(1) + f"[pause {sec}s]", s)


def long_pauses(x, thr=0.7):
    sil, t0, t1 = PF.silences(x)
    inner = [(a, b) for a, b in sil if a > t0 and b < t1]
    return sum(1 for a, b in inner if b - a >= thr), [round(b - a, 2) for a, b in inner]


def n_ends(s, lang):
    return len(re.findall(r"[。！？](?=\s*\S)", s)) if lang == "zh" else len(re.findall(r"(?<!\d)[.!?](?=\s+[A-Z\"“(])", s))


def pick(lang, n, idx, rng):
    """published clips of n different subjects: 70-150 chars (zh) / 180-400 (en), 3+ sentences, mp3 present"""
    lo, hi = (70, 150) if lang == "zh" else (180, 400)
    lessons = [l for l in idx["lessons"] if not l["id"].startswith("yuwen/")]
    rng.shuffle(lessons); out, subj = [], set()
    for l in lessons:
        s = l["id"].split("/")[0]
        if s in subj:
            continue
        t = json.loads((TRS / (l["id"].replace("/", "__") + ".json")).read_text(encoding="utf-8"))
        for c in t["clips"]:
            f = ROOT / l["repo"] / l["id"] / lang / f"{c['key']}.mp3"
            if c["lang"] == lang and lo <= len(c["send"]) <= hi and n_ends(c["send"], lang) >= 2 and f.exists():
                out.append(dict(lesson=l["id"], key=c["key"], lang=lang, send=c["send"], mp3=f)); subj.add(s); break
        if len(out) == n:
            break
    return out


def main():
    from transformers import AutoModel, AutoProcessor
    torch.backends.cuda.enable_cudnn_sdp(False)
    cfg = W.load_config(Path(__file__).resolve().parent / "tts_config.json"); PF.FFMPEG = cfg["ffmpeg"]
    OUT.mkdir(parents=True, exist_ok=True)
    idx = json.loads((TRS / "index.json").read_text(encoding="utf-8"))
    rng = random.Random(11)
    zh = pick("zh", 7, idx, rng); en = pick("en", 5, idx, rng)
    refs = {"zh": zh.pop(0), "en": en.pop(0)}           # the first clip of each language is the voice reference
    processor = AutoProcessor.from_pretrained(str(MODEL), trust_remote_code=True, codec_path=str(CODEC))
    processor.audio_tokenizer = processor.audio_tokenizer.to("cuda")
    model = AutoModel.from_pretrained(str(MODEL), trust_remote_code=True, attn_implementation="sdpa",
                                      dtype=torch.bfloat16).to("cuda").eval()
    sr_out = int(processor.model_config.sampling_rate)
    codes = {lg: processor.encode_audios_from_wav([torch.from_numpy(PF.decode(r["mp3"])).float()], PF.SR)[0]
             for lg, r in refs.items()}
    variants = [("P6", "停顿标记 0.6 秒", 0.6), ("P8", "停顿标记 0.8 秒", 0.8), ("P0", "不加标记", None)]
    items = [dict(it, n=i) for i, it in enumerate(zh + en)]
    res = {}
    for vid, label, sec in variants:
        for lang in ("zh", "en"):
            group = [(it, tr) for it in items if it["lang"] == lang for tr in range(TRIES)]
            for b in range(0, len(group), 4):
                part = group[b:b + 4]
                convs = [[processor.build_user_message(
                    text=with_pauses(it["send"], sec, lang) if sec else it["send"],
                    language="Chinese" if lang == "zh" else "English", reference=[codes[lang]])] for it, _ in part]
                batch = processor(convs, mode="generation"); t = time.time()
                with torch.no_grad():
                    out = model.generate(input_ids=batch["input_ids"].to("cuda"),
                                         attention_mask=batch["attention_mask"].to("cuda"), **GEN)
                msgs = processor.decode(out); dt = time.time() - t
                print(f"{vid} {lang}: {len(part)} clips in {dt:.0f}s", flush=True)
                for (it, tr), m in zip(part, msgs):
                    name = f"{vid}_{it['n']}_{tr + 1}"
                    if m is None:
                        res[name] = dict(v=vid, n=it["n"], tr=tr + 1, failed=True); continue
                    wav = m.audio_codes_list[0].float().mean(dim=0).numpy()
                    sf.write(OUT / f"{name}_48k.wav", wav, sr_out)
                    pcm = subprocess.run([cfg["ffmpeg"], "-v", "error", "-i", str(OUT / f"{name}_48k.wav"), "-ac", "1",
                                          "-ar", "24000", "-f", "s16le", "pipe:1"], capture_output=True, check=True).stdout
                    W.to_mp3(cfg, pcm, 24000, OUT / f"{name}.mp3")
                    x = np.frombuffer(pcm, dtype="<i2").astype("float32") / 32768
                    q = W.check_clip_qa(pcm, 24000, it["send"], lang, cfg["qa"], cfg["ffmpeg"])
                    lp, gaps = long_pauses(x)
                    res[name] = dict(v=vid, n=it["n"], tr=tr + 1, sec=round(len(x) / 24000, 1), pace=round(q.pace or 0, 2),
                                     f0=round(q.f0 or 0), long=lp, ends=n_ends(it["send"], lang),
                                     gap_med=round(float(np.median(gaps)), 2) if gaps else 0.0)
                    r = res[name]
                    print(f"  {name} {it['lesson']}: {r['sec']}s {r['pace']} c/s F0 {r['f0']}, pauses >= 0.7 s {r['long']}"
                          f" for {r['ends']} sentence ends", flush=True)
    for it in items:                                     # the published Qwen clip for comparison
        x = PF.decode(it["mp3"]); lp, _ = long_pauses(x)
        res[f"Q_{it['n']}"] = dict(v="Q", n=it["n"], long=lp, ends=n_ends(it["send"], it["lang"]),
                                   sec=round(len(x) / PF.SR, 1), pace=round(W.speech_len(it["send"], it["lang"]) / (len(x) / PF.SR), 2))
    (OUT / "results.json").write_text(json.dumps(dict(refs={k: {kk: str(vv) for kk, vv in v.items()} for k, v in refs.items()},
                                                      items=[{k: str(v) for k, v in it.items()} for it in items], results=res),
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    for vid, label in [("Q", "现在的 Qwen")] + [(v, l) for v, l, _ in variants]:
        for lang in ("zh", "en"):
            rs = [r for r in res.values() if r["v"] == vid and not r.get("failed") and items[r["n"]]["lang"] == lang]
            if rs:
                print(f"RESULT {vid} {label} {lang}: pauses >= 0.7 s {sum(r['long'] for r in rs)} for {sum(r['ends'] for r in rs)} "
                      f"sentence ends, pace {np.median([r['pace'] for r in rs]):.2f}, failed "
                      f"{sum(1 for r in res.values() if r['v'] == vid and r.get('failed'))}", flush=True)
    write_page(items, refs, res, variants)


def write_page(items, refs, res, variants):
    def cell(src, r):
        if r.get("failed"):
            return '<div class=m>没有生成出声音</div>'
        return (f'<div><audio controls preload="none" src="{src}"></audio><div class=m>{r["sec"]:.0f} 秒 · '
                f'{r["pace"]:.1f} {"字" if True else ""}/秒 · 0.7 秒以上的停顿 {r["long"]} 处（句末 {r["ends"]} 处）</div></div>')
    head = "".join(f'<div>参考录音（{ "中文" if lg == "zh" else "英文"}）：{html.escape(r["lesson"])}<br>'
                   f'<audio controls preload="none" src="../../{Path(str(r["mp3"])).relative_to(ROOT).as_posix()}"></audio></div>'
                   for lg, r in refs.items())
    secs = []
    for it in items:
        q = res[f"Q_{it['n']}"]
        rows = [f'<tr><td class=l>现在的 Qwen Serena</td><td><div class=pair>'
                f'{cell("../../" + Path(str(it["mp3"])).relative_to(ROOT).as_posix(), q)}</div></td></tr>']
        for vid, label, _ in variants:
            cells = [cell(f"{vid}_{it['n']}_{t}.mp3", res[f"{vid}_{it['n']}_{t}"]) for t in range(1, TRIES + 1)
                     if f"{vid}_{it['n']}_{t}" in res]
            rows.append(f'<tr><td class=l>MOSS 克隆 Serena · {html.escape(label)}</td><td><div class=pair>{"".join(cells)}</div></td></tr>')
        secs.append(f'<section><h2>{html.escape(it["lesson"])} <span class=m>{it["lang"]}</span></h2>'
                    f'<p class=t>{html.escape(it["send"])}</p><table>{"".join(rows)}</table></section>')
    page = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MOSS 讲解与英文</title><style>
:root{{--bg:#fafaf7;--fg:#1d1d1b;--muted:#6b6b66;--line:#e3e2dc}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161615;--fg:#ecebe6;--muted:#9a9993;--line:#2e2d2a}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 system-ui,"Microsoft YaHei",sans-serif}}
main{{max-width:1000px;margin:0 auto;padding:16px}}h1{{font-size:20px}}h2{{font-size:16px;margin:0 0 4px}}
section{{border-top:1px solid var(--line);padding:14px 0}}.t{{margin:4px 0 10px}}.m{{color:var(--muted);font-size:12px}}
table{{border-collapse:collapse;width:100%}}td{{border-bottom:1px solid var(--line);padding:6px;vertical-align:top}}
td.l{{width:200px;font-size:14px}}.pair{{display:flex;flex-wrap:wrap;gap:12px}}audio{{height:30px;width:260px}}
.refs{{display:grid;gap:8px;margin:10px 0}}
</style></head><body><main><h1>MOSS-TTS：讲解类中文和英文</h1>
<p class=m>声音克隆自网站上 Serena 的讲解录音（中文、英文各一段，见下）。句末停顿标记 0.6 秒和 0.8 秒两种，另有不加标记的版本。
每篇最上面是网站现在的 Qwen 录音。所有录音都是网站格式（24 kHz 单声道 MP3）。</p><div class=refs>{head}</div>{"".join(secs)}</main></body></html>"""
    (OUT / "listen.html").write_text(page, encoding="utf-8")
    print(f"page: {OUT / 'listen.html'}", flush=True)


if __name__ == "__main__":
    main()
