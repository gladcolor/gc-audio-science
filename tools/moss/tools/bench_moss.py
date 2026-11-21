"""Test MOSS-TTS-Local-Transformer-v1.5 (OpenMOSS, Apache 2.0) against the current Qwen3-TTS Serena recordings:
explicit pauses ([pause X.Ys]), long texts, voice cloning from a Serena recording, speed and GPU memory.
Runs in E:\\gc-audio\\venv-moss (its own torch / transformers 5). Writes E:\\gc-audio\\_test\\moss\\..., results.json and
listen.html. Run only while the GPU is free.
  E:\\gc-audio\\venv-moss\\Scripts\\python.exe bench_moss.py"""
import html, json, re, subprocess, sys, time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench_pause as BP                                 # noqa: E402  (texts, pause measures)
import pause_fix as PF                                   # noqa: E402
import tts_worker as W                                   # noqa: E402  (mp3 encoding, QA check)

ROOT = Path("E:/gc-audio")
OUT = ROOT / "_test" / "moss"
MODEL = ROOT / "models" / "MOSS-TTS-Local-Transformer-v1.5"
CODEC = ROOT / "models" / "MOSS-Audio-Tokenizer-v2"
TRIES = 2
PAUSE = 0.8                                              # the user's target at 。 and after the title / author
REF_POEM = ROOT / "_test" / "pause" / "V6_0_1.mp3"       # Serena, 春望 read slowly (2.5 chars/s)
GEN = dict(max_new_tokens=4096, do_sample=True, audio_temperature=1.7, audio_top_p=0.8, audio_top_k=25,
           audio_repetition_penalty=1.0)                 # the model card's defaults


def tagged(it):
    """title [pause] author [pause] body with a pause after every 。！？ except the last"""
    body = re.sub(r"([。！？])(?=.)", lambda m: m.group(1) + f"[pause {PAUSE}s]", it["body"])
    return f"{it['title']}[pause {PAUSE}s]{it['author']}[pause {PAUSE}s]{body}"


def plain(it):
    return it["send"]


def items():
    its = BP.texts()                                     # 春望, 钱塘湖春行, 水调歌头, 桃花源记 (two paragraphs)
    whole = json.loads((ROOT / "_test" / "whole" / "results.json").read_text(encoding="utf-8"))
    for w in whole:
        if w["title"] in ("桃花源记", "岳阳楼记"):          # the complete texts that made Qwen3-TTS stop part-way
            body = w["send"].split("。", 2)[2]
            its.append(dict(n=len(its), title=w["title"] + "（全文）", author=w["author"], body=body, send=w["send"],
                            long=True))
    return its


def main():
    from transformers import AutoModel, AutoProcessor
    torch.backends.cuda.enable_cudnn_sdp(False)
    cfg = W.load_config(Path(__file__).resolve().parent / "tts_config.json")
    PF.FFMPEG = cfg["ffmpeg"]
    qa = dict(cfg["qa"], pace=dict(cfg["qa"]["pace"], zh=[2.2, 3.0]))
    OUT.mkdir(parents=True, exist_ok=True)
    t = time.time()
    processor = AutoProcessor.from_pretrained(str(MODEL), trust_remote_code=True, codec_path=str(CODEC))
    processor.audio_tokenizer = processor.audio_tokenizer.to("cuda")      # codec weights are bf16 by default
    model = AutoModel.from_pretrained(str(MODEL), trust_remote_code=True, attn_implementation="sdpa",
                                      torch_dtype=torch.bfloat16).to("cuda").eval()
    sr_out = int(processor.model_config.sampling_rate)
    print(f"loaded in {time.time() - t:.0f}s, {torch.cuda.memory_allocated() / 2**30:.1f} GiB, output {sr_out} Hz",
          flush=True)
    ref_wav = torch.from_numpy(PF.decode(REF_POEM)).float()                   # mono 24 kHz; resampled inside
    ref_codes = processor.encode_audios_from_wav([ref_wav], PF.SR)[0]
    variants = [("M1", "MOSS：克隆 Serena + 停顿标记", tagged, True), ("M2", "MOSS：克隆 Serena，不加标记", plain, True),
                ("M3", "MOSS：自带声音 + 停顿标记", tagged, False)]
    its = items()
    res = {}
    for vid, label, fmt, clone in variants:
        group = [(it, tr) for it in its for tr in range(TRIES) if not (it.get("long") and vid == "M3")]
        for b in range(0, len(group), 4):
            part = group[b:b + 4]
            convs = [[processor.build_user_message(text=fmt(it), language="Chinese",
                                                   **({"reference": [ref_codes]} if clone else {}))] for it, _ in part]
            batch = processor(convs, mode="generation")
            torch.cuda.reset_peak_memory_stats(); t = time.time()
            with torch.no_grad():
                out = model.generate(input_ids=batch["input_ids"].to("cuda"),
                                     attention_mask=batch["attention_mask"].to("cuda"), **GEN)
            msgs = processor.decode(out)
            dt = time.time() - t
            print(f"{vid}: {len(part)} clips in {dt:.0f}s, peak {torch.cuda.max_memory_allocated() / 2**30:.1f} GiB",
                  flush=True)
            for (it, tr), m in zip(part, msgs):
                name = f"{vid}_{it['n']}_{tr + 1}"
                if m is None:
                    res[name] = dict(v=vid, n=it["n"], tr=tr + 1, failed=True); continue
                wav = m.audio_codes_list[0].float().mean(dim=0).numpy()        # stereo -> mono
                sf.write(OUT / f"{name}_48k.wav", wav, sr_out)
                r = subprocess.run([cfg["ffmpeg"], "-v", "error", "-i", str(OUT / f"{name}_48k.wav"), "-ac", "1",
                                    "-ar", "24000", "-f", "s16le", "pipe:1"], capture_output=True, check=True)
                pcm = r.stdout
                W.to_mp3(cfg, pcm, 24000, OUT / f"{name}.mp3")               # same format as the site
                x = np.frombuffer(pcm, dtype="<i2").astype("float32") / 32768
                q = W.check_clip_qa(pcm, 24000, it["send"], "zh", qa, cfg["ffmpeg"])
                res[name] = dict(v=vid, n=it["n"], tr=tr + 1, sec=round(len(x) / 24000, 1), pace=round(q.pace or 0, 2),
                                 f0=round(q.f0 or 0), gen_s=round(dt / len(part), 1), **BP.pause_metrics(it["send"], x))
                print(f"  {name} {it['title']}: {res[name]['sec']}s {res[name]['pace']} c/s, title {res[name]['title_p']}"
                      f" author {res[name]['author_p']} 。{res[name]['major_med']} ({res[name]['major_08'] * 100:.0f}% >= 0.8)"
                      f" ，{res[name]['minor_med']} F0 {res[name]['f0']}", flush=True)
    (OUT / "results.json").write_text(json.dumps(dict(texts=its, results=res), ensure_ascii=False, indent=1),
                                      encoding="utf-8")
    for vid, label, *_ in variants:
        rs = [r for r in res.values() if r["v"] == vid and not r.get("failed")]
        if rs:
            print(f"RESULT {vid} {label}: title {np.median([r['title_p'] for r in rs]):.2f}s, author "
                  f"{np.median([r['author_p'] for r in rs]):.2f}s, 。 {np.median([r['major_med'] for r in rs]):.2f}s, "
                  f">= 0.8 s {np.mean([r['major_08'] for r in rs]) * 100:.0f}%, ， {np.median([r['minor_med'] for r in rs]):.2f}s, "
                  f"pace {np.median([r['pace'] for r in rs]):.2f}, F0 {np.median([r['f0'] for r in rs]):.0f}, "
                  f"stopped part-way {sum(r['pace'] < 2.0 for r in rs)}/{len(rs)}", flush=True)
    write_page(its, res, variants)


def write_page(its, res, variants):
    def cell(src, r):
        if r.get("failed"):
            return '<div class=m>没有生成出声音</div>'
        return (f'<div><audio controls preload="none" src="{src}"></audio><div class=m>{r["sec"]:.0f} 秒 · 题目后 '
                f'{r["title_p"]:.2f} · 作者后 {r["author_p"]:.2f} · 句号处 {r["major_med"]:.2f} 秒（停够 0.8 秒 '
                f'{r["major_08"] * 100:.0f}%）· 逗号处 {r["minor_med"]:.2f} · {r["pace"]:.1f} 字/秒'
                f'{" · 中途停读" if r["pace"] < 2.0 else ""}</div></div>')
    base = json.loads((BP.OUT / "results.json").read_text(encoding="utf-8"))["results"]
    secs = []
    for it in its:
        rows = []
        if not it.get("long"):
            rows.append('<tr><td class=l>现在的 Serena（Qwen3-TTS）</td><td><div class=pair>' + "".join(
                cell(f"../pause/V0_{it['n']}_{t}.mp3", base[f"V0_{it['n']}_{t}"]) for t in (1, 2)
                if f"V0_{it['n']}_{t}" in base) + "</div></td></tr>")
        for vid, label, *_ in variants:
            cells = [cell(f"{vid}_{it['n']}_{t}.mp3", res[f"{vid}_{it['n']}_{t}"]) for t in range(1, TRIES + 1)
                     if f"{vid}_{it['n']}_{t}" in res]
            if cells:
                rows.append(f'<tr><td class=l>{html.escape(label)}</td><td><div class=pair>{"".join(cells)}</div></td></tr>')
        secs.append(f'<section><h2>{html.escape(it["title"])} · {html.escape(it["author"])}</h2>'
                    f'<p class=t>{html.escape(it["body"])}</p><table>{"".join(rows)}</table></section>')
    page = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MOSS-TTS 测试</title><style>
:root{{--bg:#fafaf7;--fg:#1d1d1b;--muted:#6b6b66;--line:#e3e2dc}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161615;--fg:#ecebe6;--muted:#9a9993;--line:#2e2d2a}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 system-ui,"Microsoft YaHei",sans-serif}}
main{{max-width:1000px;margin:0 auto;padding:16px}}h1{{font-size:20px}}h2{{font-size:16px;margin:0 0 4px}}
section{{border-top:1px solid var(--line);padding:14px 0}}.t{{margin:4px 0 10px}}.m{{color:var(--muted);font-size:12px}}
table{{border-collapse:collapse;width:100%}}td{{border-bottom:1px solid var(--line);padding:6px;vertical-align:top}}
td.l{{width:190px;font-size:14px}}.pair{{display:flex;flex-wrap:wrap;gap:12px}}audio{{height:30px;width:260px}}
</style></head><body><main><h1>MOSS-TTS v1.5 测试</h1>
<p class=m>MOSS-TTS-Local-Transformer-v1.5（开源）与现在的 Qwen3-TTS Serena 对比。克隆用的参考录音：Serena 朗读的《春望》。
"停顿标记"＝在题目、作者后和每个句号后写 [pause 0.8s]。所有录音都转成网站的格式（24 kHz 单声道 MP3，−16 LUFS）。
最后两篇是全文（400 多字），Qwen3-TTS 读这类长文经常中途停读。</p>{"".join(secs)}</main></body></html>"""
    (OUT / "listen.html").write_text(page, encoding="utf-8")
    print(f"page: {OUT / 'listen.html'}", flush=True)


if __name__ == "__main__":
    main()
