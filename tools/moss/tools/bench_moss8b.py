"""MOSS-TTS round 4: the 8B v1.5 model ("recommended for production", 24 kHz mono) compressed to 8 bits with
bitsandbytes, against the 4B Local v1.5 results of round 3 (same texts, same Serena references, same pause markers and
target durations) and round 2 (English with [pause 0.8s]). Runs in E:\\gc-audio\\venv-moss.
Writes E:\\gc-audio\\_test\\moss8b\\..., results.json, listen.html.
  E:\\gc-audio\\venv-moss\\Scripts\\python.exe bench_moss8b.py [4bit]"""
import html, json, subprocess, sys, time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench_moss2 as B2                                 # noqa: E402
import bench_moss3 as B3                                 # noqa: E402
import pause_fix as PF                                   # noqa: E402
import tts_worker as W                                   # noqa: E402

ROOT = Path("E:/gc-audio")
FOUR = "4bit" in sys.argv
OUT = ROOT / "_test" / ("moss8b4" if FOUR else "moss8b")
MODEL = ROOT / "models" / "MOSS-TTS-v1.5"
CODEC = ROOT / "models" / "MOSS-Audio-Tokenizer"
TRIES = 2


def main():
    from transformers import AutoModel, AutoProcessor, BitsAndBytesConfig
    torch.backends.cuda.enable_cudnn_sdp(False)
    cfg = W.load_config(Path(__file__).resolve().parent / "tts_config.json"); PF.FFMPEG = cfg["ffmpeg"]
    OUT.mkdir(parents=True, exist_ok=True)
    its, expl_ref = B3.items()
    m2 = json.loads((ROOT / "_test" / "moss2" / "results.json").read_text(encoding="utf-8"))
    en = [dict(kind="en", label="英文（模型自然语速）", pace=None,
               it=dict(title=it["lesson"], author="", body=it["send"], send=it["send"], mp3=it["mp3"], n2=it["n"]))
          for it in m2["items"] if it["lang"] == "en"][:2]
    its = its + en
    if "poems" in sys.argv:                            # quick speed check: the 4 short-poem items only
        its = its[:4]
    t = time.time()
    processor = AutoProcessor.from_pretrained(str(MODEL), trust_remote_code=True, codec_path=str(CODEC))
    processor.audio_tokenizer = processor.audio_tokenizer.to("cuda")
    q = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_quant_type="nf4") if FOUR \
        else BitsAndBytesConfig(load_in_8bit=True)
    model = AutoModel.from_pretrained(str(MODEL), trust_remote_code=True, attn_implementation="sdpa", dtype=torch.bfloat16,
                                      quantization_config=q, device_map="cuda:0").eval()
    sr_out = int(processor.model_config.sampling_rate)
    print(f"loaded in {time.time() - t:.0f}s, {torch.cuda.memory_allocated() / 2**30:.1f} GiB, {sr_out} Hz, "
          f"{'4-bit' if FOUR else '8-bit'}", flush=True)
    enc = lambda f: processor.encode_audios_from_wav([torch.from_numpy(PF.decode(Path(f))).float()[None, :]], PF.SR)[0]   # [channels, samples]
    refs = {"poem": enc(ROOT / "_test" / "pause" / "V6_0_1.mp3"), "expl": enc(expl_ref), "en": enc(m2["refs"]["en"]["mp3"])}
    jobs = []
    for i, e in enumerate(its):
        it = e["it"]
        if e["kind"] == "poem":
            text = f"{it['title']}[pause 1.0s]{it['author']}[pause 1.0s]" + B2.with_pauses(it["body"], 0.8, "zh")
        else:
            text = B2.with_pauses(it["send"], 0.8, "zh" if e["kind"] == "expl" else "en")
        tok = B3.target_tokens(it["send"], "zh", e["pace"], text) if e["pace"] else None
        for tr in range(TRIES):
            jobs.append((i, e, tr, text, tok))
    res = {}
    for b in range(0, len(jobs), 4):
        part = jobs[b:b + 4]
        convs = [[processor.build_user_message(text=text, language="English" if e["kind"] == "en" else "Chinese",
                                               reference=[refs[e["kind"]]], **({"tokens": tok} if tok else {}))]
                 for i, e, tr, text, tok in part]
        batch = processor(convs, mode="generation"); torch.cuda.reset_peak_memory_stats(); t = time.time()
        with torch.no_grad():
            out = model.generate(input_ids=batch["input_ids"].to("cuda"), attention_mask=batch["attention_mask"].to("cuda"),
                                 max_new_tokens=4096, audio_temperature=1.7, audio_top_p=0.8, audio_top_k=25,
                                 audio_repetition_penalty=1.0)
        msgs = processor.decode(out); dt = time.time() - t
        print(f"batch {b // 4 + 1}: {len(part)} clips in {dt:.0f}s, peak {torch.cuda.max_memory_allocated() / 2**30:.1f} GiB", flush=True)
        for (i, e, tr, text, tok), m in zip(part, msgs):
            name = f"{i}_{tr + 1}"
            if m is None:
                res[name] = dict(i=i, tr=tr + 1, failed=True); continue
            wav = m.audio_codes_list[0].float().reshape(-1).cpu().numpy()
            sf.write(OUT / f"{name}_raw.wav", wav, sr_out)
            pcm = subprocess.run([cfg["ffmpeg"], "-v", "error", "-i", str(OUT / f"{name}_raw.wav"), "-ac", "1", "-ar", "24000",
                                  "-f", "s16le", "pipe:1"], capture_output=True, check=True).stdout
            W.to_mp3(cfg, pcm, 24000, OUT / f"{name}.mp3")
            x = np.frombuffer(pcm, dtype="<i2").astype("float32") / 32768
            sec = len(x) / 24000; lang = "en" if e["kind"] == "en" else "zh"
            qa = W.check_clip_qa(pcm, 24000, e["it"]["send"], lang, cfg["qa"], cfg["ffmpeg"])
            lp, _ = B2.long_pauses(x)
            res[name] = dict(i=i, tr=tr + 1, sec=round(sec, 1), target=round(tok / 12.5, 1) if tok else None,
                             pace=round(W.speech_len(e["it"]["send"], lang) / sec, 2), f0=round(qa.f0 or 0), long=lp,
                             ends=B2.n_ends(e["it"]["send"], lang) + (2 if e["kind"] == "poem" else 0), gen_s=round(dt / len(part), 1))
            r = res[name]
            print(f"  {name} {e['label']} {e['it']['title']}: {r['sec']}s (target {r['target']}), pace {r['pace']}, "
                  f"F0 {r['f0']}, long pauses {lp}/{r['ends']}", flush=True)
    (OUT / "results.json").write_text(json.dumps(dict(results=res), ensure_ascii=False, indent=1), encoding="utf-8")
    ok = [r for r in res.values() if not r.get("failed")]
    print(f"RESULT {'4-bit' if FOUR else '8-bit'} 8B: {len(ok)}/{len(res)} generated, long pauses "
          f"{sum(r['long'] for r in ok)}/{sum(r['ends'] for r in ok)}, mean generation time per clip "
          f"{np.mean([r['gen_s'] for r in ok]):.1f}s", flush=True)
    write_page(its, res)


def write_page(its, res):
    def cell(src, r, label):
        if not r:
            return ""
        if r.get("failed"):
            return f'<div class=m>{label}：没有生成出声音</div>'
        tgt = f"（目标 {r['target']:.0f} 秒）" if r.get("target") else ""
        return (f'<div><div class=m>{label}</div><audio controls preload="none" src="{src}"></audio><div class=m>'
                f'{r["sec"]:.0f} 秒{tgt} · {r["pace"]:.2f}/秒 · 0.7 秒以上停顿 {r["long"]} 处</div></div>')
    m3 = json.loads((ROOT / "_test" / "moss3" / "results.json").read_text(encoding="utf-8"))["results"]
    m2 = json.loads((ROOT / "_test" / "moss2" / "results.json").read_text(encoding="utf-8"))["results"]
    secs = []
    for i, e in enumerate(its):
        if e["kind"] == "en":
            n2 = e["it"]["n2"]
            local = [cell(f"../moss2/P8_{n2}_{t}.mp3", m2.get(f"P8_{n2}_{t}"), f"4B Local · 第 {t} 次") for t in (1, 2)]
        else:
            local = [cell(f"../moss3/{i}_T_{t}.mp3", m3.get(f"{i}_T_{t}"), f"4B Local · 第 {t} 次") for t in (1, 2)]
        big = [cell(f"{i}_{t}.mp3", res.get(f"{i}_{t}"), f"8B 压缩版 · 第 {t} 次") for t in (1, 2)]
        secs.append(f'<section><h2>{html.escape(e["label"])} · {html.escape(e["it"]["title"])}</h2><p class=t>{html.escape(e["it"]["body"])}</p>'
                    f'<div class=pair>{"".join(local)}</div><div class=pair>{"".join(big)}</div></section>')
    page = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MOSS 8B 与 4B</title><style>
:root{{--bg:#fafaf7;--fg:#1d1d1b;--muted:#6b6b66;--line:#e3e2dc}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161615;--fg:#ecebe6;--muted:#9a9993;--line:#2e2d2a}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 system-ui,"Microsoft YaHei",sans-serif}}
main{{max-width:1000px;margin:0 auto;padding:16px}}h1{{font-size:20px}}h2{{font-size:16px;margin:0 0 4px}}
section{{border-top:1px solid var(--line);padding:14px 0}}.t{{margin:4px 0 10px}}.m{{color:var(--muted);font-size:12px}}
.pair{{display:flex;flex-wrap:wrap;gap:16px;margin:6px 0}}audio{{height:30px;width:280px}}
</style></head><body><main><h1>MOSS-TTS：8B 主模型（{'4' if FOUR else '8'} 位压缩）与 4B Local 版</h1>
<p class=m>同样的文字、同样的 Serena 参考录音、同样的停顿标记和目标语速。每篇上面一行是 4B Local 版，下面一行是 8B 压缩版。
都转成网站格式（24 kHz 单声道 MP3）。</p>{"".join(secs)}</main></body></html>"""
    (OUT / "listen.html").write_text(page, encoding="utf-8")
    print(f"page: {OUT / 'listen.html'}", flush=True)


if __name__ == "__main__":
    main()
