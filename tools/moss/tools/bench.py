"""Speed test for Qwen3-TTS on this PC: single requests vs batched requests (one model), real lesson sentences.
  python bench.py single  <transcript.json> [tag]
  python bench.py batch   <transcript.json> <batch size> [tag]
Writes the audio to <root>/_test/bench/ and prints audio seconds, wall seconds, pace and throughput."""
import json, sys, time, wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tts_worker as W                                   # noqa: E402


def pick(path, n=6):
    clips = json.loads(Path(path).read_text(encoding="utf-8"))["clips"]
    out = []
    for lang in ("en", "zh"):
        cs = sorted((c for c in clips if c["lang"] == lang), key=lambda c: len(c["send"]))
        out += cs if n >= len(cs) else [cs[int(i * len(cs) / n)] for i in range(n)]
    return out


def save(out, name, a, sr):
    import numpy as np
    a = np.asarray(a).reshape(-1)
    pcm = (np.clip(a.astype("float32"), -1, 1) * 32767).astype("<i2").tobytes()
    with wave.open(str(out / name), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm)
    return len(pcm) / 2 / sr


def main():
    mode, path = sys.argv[1], sys.argv[2]
    bs = int(sys.argv[3]) if mode == "batch" else 1
    tag = sys.argv[4] if mode == "batch" and len(sys.argv) > 4 else (sys.argv[3] if mode == "single" and len(sys.argv) > 3 else "")
    cfg = W.load_config(Path(__file__).resolve().parent / "tts_config.json")
    import os
    cfg["decode_one_by_one"] = os.environ.get("DECODE_ONE", "") == "1"
    out = Path(cfg["root"]) / "_test" / "bench"; out.mkdir(parents=True, exist_ok=True)
    import torch
    t0 = time.time(); model = W.load_model(cfg); print(f"load {time.time() - t0:.0f}s", flush=True)
    model.generate_custom_voice(text="Warm up.", language="English", speaker=cfg["speaker"], max_new_tokens=100)
    clips = pick(path, max(6, bs))
    groups = []
    for lang in ("en", "zh"):                            # batches of one language, similar length (clips are sorted)
        cs = [c for c in clips if c["lang"] == lang]
        groups += [cs[i:i + bs] for i in range(0, len(cs), bs)]
    tot_audio, odd, t_all = 0.0, 0, time.time()
    for g in groups:
        lang = g[0]["lang"]
        t = time.time()
        wavs, sr = model.generate_custom_voice(
            text=[c["send"] for c in g], language=[W.LANG_NAME[lang]] * len(g), speaker=[cfg["speaker"]] * len(g),
            max_new_tokens=max(W.max_tokens(c["send"], lang) for c in g))
        dt = time.time() - t
        for c, a in zip(g, wavs):
            sec = save(out, f"{mode}{bs}{tag}_{lang}_{c['key']}.wav", a, sr)
            cps = len(c["send"]) / max(sec, 0.1); lo, hi = W.PACE[lang]; ok = lo <= cps <= hi
            odd += not ok; tot_audio += sec
            print(f"  {lang} {len(c['send']):4d} chars  {sec:5.1f}s audio  {cps:5.1f} c/s {'normal' if ok else 'ODD'}", flush=True)
        print(f" batch of {len(g)}: {dt:.1f}s wall", flush=True)
    wall = time.time() - t_all
    print(f"RESULT {mode} bs={bs}{' ' + tag if tag else ''}: {tot_audio:.0f}s audio in {wall:.0f}s wall = "
          f"{tot_audio / wall:.2f}x realtime, decode {model.decode_s:.0f}s (one by one: {cfg['decode_one_by_one']}), odd {odd}, peak GPU mem {torch.cuda.max_memory_allocated() / 2**30:.1f} GB",
          flush=True)


if __name__ == "__main__":
    main()
