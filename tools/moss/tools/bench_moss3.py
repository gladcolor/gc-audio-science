"""MOSS-TTS round 3: duration control. The target length of each clip is computed from the pace the user wants
(short poems 2.5 chars/s, long texts 3.0, cheerful +0.2, somber -0.2; explanations 4.0, science 3.8, everyday life 4.1,
with [pause 0.8s] after sentence ends) and passed to the model as `tokens` (12.5 per second). Each text is also
recorded without duration control for comparison. Voice: Serena cloned (poem reference for poems, the explanatory
reference of round 2 for explanations). Runs in E:\\gc-audio\\venv-moss. Writes E:\\gc-audio\\_test\\moss3\\.
  E:\\gc-audio\\venv-moss\\Scripts\\python.exe bench_moss3.py"""
import html, json, re, subprocess, sys, time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench_moss2 as B2                                 # noqa: E402  (pause tags, pause counting)
import bench_pause as BP                                 # noqa: E402
import pause_fix as PF                                   # noqa: E402
import tts_worker as W                                   # noqa: E402

ROOT = Path("E:/gc-audio")
OUT = ROOT / "_test" / "moss3"
TRIES = 2
PAUSE = 0.8
GEN = B2.GEN


def target_tokens(send, lang, pace, text):
    """frames for the whole clip at `pace` chars/s - the user's pace includes the pauses (as on the listening pages);
    never shorter than the tagged pauses plus the text at 6 chars/s"""
    tags = sum(float(x) for x in re.findall(r"\[pause ([\d.]+)s\]", text))
    sec = max(W.speech_len(send, lang) / pace, tags + W.speech_len(send, lang) / 6.0)
    return int(round(sec * 12.5))


def items():
    its = BP.texts()                                     # 春望 (somber), 钱塘湖春行 (cheerful), 水调歌头, 桃花源记 2 paragraphs
    out = [dict(kind="poem", label="短诗 2.5", pace=2.5, it=its[0]), dict(kind="poem", label="短诗·悲沉 2.3", pace=2.3, it=its[0]),
           dict(kind="poem", label="短诗 2.5", pace=2.5, it=its[1]), dict(kind="poem", label="短诗·轻快 2.7", pace=2.7, it=its[1]),
           dict(kind="poem", label="长文 3.0", pace=3.0, it=its[3])]
    m2 = json.loads((ROOT / "_test" / "moss2" / "results.json").read_text(encoding="utf-8"))
    pace_by = {"math": 3.8, "biology": 3.8, "cs": 3.8, "earth": 3.8, "physics": 3.8, "chemistry": 3.8, "astronomy": 3.8,
               "politics": 4.0, "ushistory": 4.0, "economics": 4.1, "georgia": 4.0}
    for it in m2["items"]:
        if it["lang"] != "zh":
            continue
        subj = it["lesson"].split("/")[0]
        p = pace_by.get(subj, 4.0)
        out.append(dict(kind="expl", label=f"讲解 {p}（{'理科' if p == 3.8 else '生活' if p == 4.1 else '一般'}）", pace=p,
                        it=dict(title=it["lesson"], author="", body=it["send"], send=it["send"], mp3=it["mp3"])))
    return out, m2["refs"]["zh"]["mp3"]


def main():
    from transformers import AutoModel, AutoProcessor
    torch.backends.cuda.enable_cudnn_sdp(False)
    cfg = W.load_config(Path(__file__).resolve().parent / "tts_config.json"); PF.FFMPEG = cfg["ffmpeg"]
    OUT.mkdir(parents=True, exist_ok=True)
    its, expl_ref = items()
    processor = AutoProcessor.from_pretrained(str(B2.MODEL), trust_remote_code=True, codec_path=str(B2.CODEC))
    processor.audio_tokenizer = processor.audio_tokenizer.to("cuda")
    model = AutoModel.from_pretrained(str(B2.MODEL), trust_remote_code=True, attn_implementation="sdpa",
                                      dtype=torch.bfloat16).to("cuda").eval()
    sr_out = int(processor.model_config.sampling_rate)
    enc = lambda f: processor.encode_audios_from_wav([torch.from_numpy(PF.decode(Path(f))).float()], PF.SR)[0]
    refs = {"poem": enc(ROOT / "_test" / "pause" / "V6_0_1.mp3"), "expl": enc(expl_ref)}
    jobs = []
    for i, e in enumerate(its):
        if e["kind"] == "expl":
            text = B2.with_pauses(e["it"]["send"], PAUSE, "zh")
        else:                                            # poems: also after the title and the author (the user)
            it = e["it"]
            text = f"{it['title']}[pause 1.0s]{it['author']}[pause 1.0s]" + B2.with_pauses(it["body"], PAUSE, "zh")
        for mode in ("T", "F"):                          # T: duration control, F: free
            for tr in range(TRIES):
                jobs.append((i, e, mode, tr, text, target_tokens(e["it"]["send"], "zh", e["pace"], text) if mode == "T" else None))
    res = {}
    for b in range(0, len(jobs), 4):
        part = jobs[b:b + 4]
        convs = [[processor.build_user_message(text=text, language="Chinese", reference=[refs[e["kind"]]],
                                               **({"tokens": tok} if tok else {}))] for i, e, mode, tr, text, tok in part]
        batch = processor(convs, mode="generation"); t = time.time()
        with torch.no_grad():
            out = model.generate(input_ids=batch["input_ids"].to("cuda"), attention_mask=batch["attention_mask"].to("cuda"), **GEN)
        msgs = processor.decode(out)
        print(f"batch {b // 4 + 1}: {len(part)} clips in {time.time() - t:.0f}s", flush=True)
        for (i, e, mode, tr, text, tok), m in zip(part, msgs):
            name = f"{i}_{mode}_{tr + 1}"
            if m is None:
                res[name] = dict(i=i, mode=mode, tr=tr + 1, failed=True); continue
            wav = m.audio_codes_list[0].float().mean(dim=0).numpy()
            sf.write(OUT / f"{name}_48k.wav", wav, sr_out)
            pcm = subprocess.run([cfg["ffmpeg"], "-v", "error", "-i", str(OUT / f"{name}_48k.wav"), "-ac", "1", "-ar", "24000",
                                  "-f", "s16le", "pipe:1"], capture_output=True, check=True).stdout
            W.to_mp3(cfg, pcm, 24000, OUT / f"{name}.mp3")
            x = np.frombuffer(pcm, dtype="<i2").astype("float32") / 32768
            sec = len(x) / 24000
            q = W.check_clip_qa(pcm, 24000, e["it"]["send"], "zh", cfg["qa"], cfg["ffmpeg"])
            lp, gaps = B2.long_pauses(x)
            speech = sec - sum(g for g in gaps if g >= 0.7)          # time without the long pauses
            res[name] = dict(i=i, mode=mode, tr=tr + 1, sec=round(sec, 1), target=round(tok / 12.5, 1) if tok else None,
                             pace=round(W.speech_len(e["it"]["send"], "zh") / sec, 2),
                             pace_speech=round(W.speech_len(e["it"]["send"], "zh") / max(speech, 0.1), 2),
                             f0=round(q.f0 or 0), long=lp)
            r = res[name]
            print(f"  {name} {e['label']} {e['it']['title']}: {r['sec']}s (target {r['target']}), pace {r['pace']} "
                  f"(want {e['pace']}), F0 {r['f0']}, long pauses {lp}", flush=True)
    (OUT / "results.json").write_text(json.dumps(dict(items=[{k: (v if k != "it" else {kk: str(vv) for kk, vv in v.items()})
                                                               for k, v in e.items()} for e in its], results=res),
                                                 ensure_ascii=False, indent=1), encoding="utf-8")
    for mode, lab in (("T", "duration control"), ("F", "free")):
        errs = [abs(r["pace"] - its[r["i"]]["pace"]) / its[r["i"]]["pace"] for r in res.values() if r["mode"] == mode and not r.get("failed")]
        print(f"RESULT {lab}: pace within 5% of the target {sum(e <= 0.05 for e in errs)}/{len(errs)}, median error "
              f"{np.median(errs) * 100:.0f}%, failed {sum(1 for r in res.values() if r['mode'] == mode and r.get('failed'))}", flush=True)
    write_page(its, res)


def write_page(its, res):
    def cell(name):
        r = res.get(name)
        if not r:
            return ""
        if r.get("failed"):
            return '<div class=m>没有生成出声音</div>'
        tgt = f"（目标 {r['target']:.0f} 秒）" if r["target"] else ""
        return (f'<div><audio controls preload="none" src="{name}.mp3"></audio><div class=m>{r["sec"]:.0f} 秒{tgt} · '
                f'{r["pace"]:.2f} 字/秒 · 0.7 秒以上停顿 {r["long"]} 处</div></div>')
    secs = []
    for i, e in enumerate(its):
        rows = [f'<tr><td class=l>按目标语速 {e["pace"]}</td><td><div class=pair>{cell(f"{i}_T_1")}{cell(f"{i}_T_2")}</div></td></tr>',
                f'<tr><td class=l>不控制时长</td><td><div class=pair>{cell(f"{i}_F_1")}{cell(f"{i}_F_2")}</div></td></tr>']
        secs.append(f'<section><h2>{html.escape(e["label"])} · {html.escape(e["it"]["title"])}</h2>'
                    f'<p class=t>{html.escape(e["it"]["body"])}</p><table>{"".join(rows)}</table></section>')
    page = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MOSS 语速控制</title><style>
:root{{--bg:#fafaf7;--fg:#1d1d1b;--muted:#6b6b66;--line:#e3e2dc}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161615;--fg:#ecebe6;--muted:#9a9993;--line:#2e2d2a}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 system-ui,"Microsoft YaHei",sans-serif}}
main{{max-width:1000px;margin:0 auto;padding:16px}}h1{{font-size:20px}}h2{{font-size:16px;margin:0 0 4px}}
section{{border-top:1px solid var(--line);padding:14px 0}}.t{{margin:4px 0 10px}}.m{{color:var(--muted);font-size:12px}}
table{{border-collapse:collapse;width:100%}}td{{border-bottom:1px solid var(--line);padding:6px;vertical-align:top}}
td.l{{width:150px;font-size:14px}}.pair{{display:flex;flex-wrap:wrap;gap:12px}}audio{{height:30px;width:260px}}
</style></head><body><main><h1>MOSS-TTS：按目标语速录音</h1>
<p class=m>按你定的语速算出每条的目标时长，交给 MOSS 的时长控制；下面一行是同样文字不控制时长的版本。克隆 Serena。
诗词在题目、作者后加 [pause 1.0s]，每个句号后加 [pause 0.8s]；讲解在句末加 [pause 0.8s]。语速按全长计算（含停顿）。</p>{"".join(secs)}</main></body></html>"""
    (OUT / "listen.html").write_text(page, encoding="utf-8")
    print(f"page: {OUT / 'listen.html'}", flush=True)


if __name__ == "__main__":
    main()
