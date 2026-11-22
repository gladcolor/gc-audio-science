"""Speed + quality test of the CUDA-graph batched path (qwen3-tts-triton "faster" runner on faster-qwen3-tts 0.3.2),
run with E:\\gc-audio\\venv-fast. Same sentences and sampling as bench_sampling.py's T0.5-S0.5 (temperature 0.5 for
talker and sub-talker, top_k 50, top_p 1.0, repetition penalty 1.05), so the two can be compared clip by clip.
  python bench_cg.py <transcript.json> [batch_size] [runner]"""
import json, sys, time, wave
from pathlib import Path

import numpy as np

PACE = {"en": (7.0, 22.0), "zh": (2.8, 9.0)}
EST = {"en": 11.0, "zh": 4.0}
ROOT = Path("E:/gc-audio")
MODEL = str(ROOT / "models" / "Qwen3-TTS-12Hz-1.7B-CustomVoice")


def cap(texts, lang):                                   # same per-batch cap as tts_worker.batch_tokens
    sec = max(4.0, max(len(t) for t in texts) / EST[lang] * 1.7 + 2.0)
    return int(sec * 12.5) + 10


def main():
    path = sys.argv[1]
    bs = int(sys.argv[2]) if len(sys.argv) > 2 else 32
    runner_name = sys.argv[3] if len(sys.argv) > 3 else "faster"
    out = ROOT / "_test" / "bench"; out.mkdir(parents=True, exist_ok=True)
    clips = json.loads(Path(path).read_text(encoding="utf-8"))["clips"]
    zh = sorted((c for c in clips if c["lang"] == "zh"), key=lambda c: len(c["send"]))
    zh = [zh[int(i * len(zh) / 32)] for i in range(32)]
    en = sorted((c for c in clips if c["lang"] == "en"), key=lambda c: len(c["send"]))
    en = [en[int(i * len(en) / 8)] for i in range(8)]
    import torch
    from qwen3_tts_triton import create_runner
    t0 = time.time()
    r = create_runner(runner_name, model_id=MODEL)
    r.load_model()
    print(f"load {time.time() - t0:.0f}s", flush=True)
    kw = dict(batch_size=bs, temperature=0.5, top_k=50, top_p=1.0, repetition_penalty=1.05, bucket=True)
    for lang, group in (("zh", zh), ("en", en)):     # first call per language: CUDA-graph capture (timed separately)
        t = time.time()
        r.generate_batch([c["send"] for c in group[:2]], language=lang, speaker="serena", max_new_tokens=60, **kw)
        print(f"warm-up / graph capture {lang}: {time.time() - t:.0f}s", flush=True)
    tag = f"CG-{runner_name}-bs{bs}"
    for lang, group in (("zh", zh), ("en", en)):
        texts = [c["send"] for c in group]
        torch.cuda.synchronize(); t = time.time()
        res = r.generate_batch(texts, language=lang, speaker="serena", max_new_tokens=cap(texts, lang), **kw)
        torch.cuda.synchronize(); dt = time.time() - t
        cps, odd, total = [], 0, 0.0
        for c, item in zip(group, res["results"]):
            a = np.asarray(item["audio"], dtype="float32").reshape(-1); sr = int(item["sample_rate"])
            pcm = (np.clip(a, -1, 1) * 32767).astype("<i2").tobytes()
            with wave.open(str(out / f"{tag}_{lang}_{c['key']}.wav"), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm)
            sec = len(pcm) / 2 / sr; total += sec; v = len(c["send"]) / max(sec, 0.1); cps.append(v)
            lo, hi = PACE[lang]; odd += not (lo <= v <= hi)
        cps.sort()
        print(f"RESULT {tag} {lang} n={len(cps)}: {total:.0f}s audio in {dt:.1f}s = {total / dt:.2f}x real time | pace "
              f"median {cps[len(cps)//2]:.1f} min {cps[0]:.1f} max {cps[-1]:.1f} odd {odd} | peak VRAM "
              f"{torch.cuda.max_memory_allocated() / 2**30:.1f} GB", flush=True)


if __name__ == "__main__":
    main()
