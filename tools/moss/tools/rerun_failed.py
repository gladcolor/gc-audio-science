"""Record again the whole-text test clips that failed (the model stopped reading part-way and the clip stayed silent
until the cap). Same settings and instruction as the failed clip; up to 3 tries each. A try succeeds when the pace is
2.2-4.0 characters/s, the clip ends within 3 s of the last speech and has no silence of 4 s or more. A success
replaces the file; results.json and listen.html of the whole-text test are updated. Run only while the GPU is free.
  python rerun_failed.py"""
import json, sys, time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench_whole as BW                                 # noqa: E402
import tts_worker as W                                   # noqa: E402

OUT = BW.OUT
ROUNDS = 3


def silence_profile(x, sr):
    """(trailing silence s, longest inner silence s) from 0.1 s frames"""
    n = sr // 10; k = len(x) // n
    db = 20 * np.log10(np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(1)) + 1e-9)
    loud = db > np.percentile(db, 90) - 35
    idx = np.where(loud)[0]
    if not len(idx):
        return len(x) / sr, len(x) / sr
    trail = (k - 1 - idx[-1]) / 10
    gaps = np.diff(idx) - 1
    return trail, (gaps.max() / 10 if len(gaps) else 0.0)


def main():
    cfg = W.load_config(Path(__file__).resolve().parent / "tts_config.json")
    cfg["decode_one_by_one"] = True; cfg["gpu_mem_fraction"] = 0.9
    qa = dict(cfg["qa"], pace=dict(cfg["qa"]["pace"], zh=[3.0, 6.5]))
    items = json.loads((OUT / "results.json").read_text(encoding="utf-8"))
    ins = dict(BW.SETTINGS)
    todo = [(it, k) for it in items for k, v in sorted(it["tries"].items()) if v["pace"] < 2.2 or v["capped"]]
    print(f"{len(todo)} failed clips: " + ", ".join(f"{it['title']} {k}" for it, k in todo), flush=True)
    model = W.load_model(cfg)
    model.generate_custom_voice(text="预热。", language="Chinese", speaker=cfg["speaker"], max_new_tokens=60)
    attempts = {f"{it['n']}_{k}": 0 for it, k in todo}
    for rnd in range(1, ROUNDS + 1):
        if not todo:
            break
        left = []
        for s in ("A", "B"):                             # one instruction per batch
            group = [(it, k) for it, k in todo if k[0] == s]
            for b in range(0, len(group), 4):
                part = group[b:b + 4]
                texts = [it["send"] for it, _ in part]
                kw = dict(W.gen_kwargs(cfg))
                if ins[s]:
                    kw["instruct"] = [ins[s]] * len(texts)
                cap = int((max(len(t) for t in texts) / 2.0 + 10) * W.CODEC_HZ)   # 2.0 chars/s is already too slow
                t = time.time()
                wavs, sr = model.generate_custom_voice(text=texts, language=["Chinese"] * len(texts),
                                                       speaker=[cfg["speaker"]] * len(texts), max_new_tokens=cap, **kw)
                print(f"round {rnd} {s}: {len(part)} clips in {time.time() - t:.0f}s", flush=True)
                for (it, k), a in zip(part, wavs):
                    attempts[f"{it['n']}_{k}"] += 1
                    pcm = W.pcm16(a); sec = len(pcm) / 2 / sr
                    x = np.frombuffer(pcm, dtype="<i2").astype("float32") / 32768
                    trail, gap = silence_profile(x, sr)
                    pace = W.speech_len(it["send"], "zh") / sec
                    good = 2.2 <= pace <= 4.0 and trail < 3 and gap < 4
                    print(f"  {it['title']} {k}: {sec:.0f}s, {pace:.2f} c/s, trailing silence {trail:.1f}s, "
                          f"longest gap {gap:.1f}s -> {'OK' if good else 'failed again'}", flush=True)
                    if good:
                        W.to_mp3(cfg, pcm, sr, OUT / f"{it['n']:02d}_{k}.mp3")
                        q = W.check_clip_qa(pcm, sr, it["send"], "zh", qa, cfg["ffmpeg"])
                        it["tries"][k] = dict(sec=round(sec, 1), pace=round(q.pace or 0, 2), f0=round(q.f0 or 0, 1),
                                              ok=not q.reasons, capped=False,
                                              windows=BW.f0_windows(pcm, sr, cfg["ffmpeg"]),
                                              redone=attempts[f"{it['n']}_{k}"])
                    else:
                        left.append((it, k))
        todo = left
    (OUT / "results.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    BW.write_page(items)
    print("RESULT attempts per clip: " + ", ".join(f"{k}: {v}" for k, v in attempts.items())
          + f"; still failed: {len(todo)}", flush=True)


if __name__ == "__main__":
    main()
