"""A/B test of sampling settings for voice stability: the same Chinese (and a few English) sentences, batch of 32,
with several temperature settings. Writes <root>/_test/bench/<setting>_<lang>_<key>.wav and prints pace per setting.
  python bench_sampling.py <transcript.json>"""
import json, sys, time, wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tts_worker as W                                   # noqa: E402

SETTINGS = [                                             # name -> generate kwargs (default checkpoint: 0.9 / 0.9)
    ("T0.9-S0.9", {}),
    ("T0.7-S0.7", {"temperature": 0.7, "subtalker_temperature": 0.7}),
    ("T0.5-S0.5", {"temperature": 0.5, "subtalker_temperature": 0.5}),
    ("T0.9-Sgreedy", {"subtalker_dosample": False}),
    ("T0.5-Sgreedy", {"temperature": 0.5, "subtalker_dosample": False}),
    ("T0.6-S0.6", {"temperature": 0.6, "subtalker_temperature": 0.6}),
    ("T0.55-S0.55", {"temperature": 0.55, "subtalker_temperature": 0.55}),
]


def main():
    cfg = W.load_config(Path(__file__).resolve().parent / "tts_config.json")
    cfg["decode_one_by_one"] = True
    cfg["gpu_mem_fraction"] = 0.9                        # the worker is paused: this test may use the whole GPU
    only = set(sys.argv[2:])                             # optional: names of the settings to run
    out = Path(cfg["root"]) / "_test" / "bench"; out.mkdir(parents=True, exist_ok=True)
    import numpy as np
    model = W.load_model(cfg)
    model.generate_custom_voice(text="Warm up.", language="English", speaker=cfg["speaker"], max_new_tokens=100)
    clips = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["clips"]
    zh = sorted((c for c in clips if c["lang"] == "zh"), key=lambda c: len(c["send"]))
    zh = [zh[int(i * len(zh) / 32)] for i in range(32)]  # 32 Chinese sentences, short to long
    en = sorted((c for c in clips if c["lang"] == "en"), key=lambda c: len(c["send"]))
    en = [en[int(i * len(en) / 8)] for i in range(8)]    # 8 English for comparison
    for name, kw in SETTINGS:
        if only and name not in only:
            continue
        for lang, group in (("zh", zh), ("en", en)):
            texts = [c["send"] for c in group]
            t = time.time()
            wavs, sr = model.generate_custom_voice(text=texts, language=[W.LANG_NAME[lang]] * len(texts),
                                                   speaker=[cfg["speaker"]] * len(texts),
                                                   max_new_tokens=W.batch_tokens(texts, lang), **kw)
            dt = time.time() - t
            cps, odd = [], 0
            for c, a in zip(group, wavs):
                a = np.asarray(a).reshape(-1)
                pcm = (np.clip(a.astype("float32"), -1, 1) * 32767).astype("<i2").tobytes()
                with wave.open(str(out / f"{name}_{lang}_{c['key']}.wav"), "wb") as w:
                    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm)
                sec = len(pcm) / 2 / sr; v = len(c["send"]) / max(sec, 0.1); cps.append(v)
                lo, hi = W.PACE[lang]; odd += not (lo <= v <= hi)
            cps.sort()
            print(f"RESULT {name:13s} {lang} n={len(cps)}  pace median {cps[len(cps)//2]:5.1f} c/s  "
                  f"min {cps[0]:4.1f} max {cps[-1]:4.1f}  odd {odd}  ({dt:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
