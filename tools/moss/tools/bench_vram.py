"""GPU memory and time vs batch size and clip length, for planning batches.
Each run forces exactly T generation steps for every clip in the batch (min_new_tokens = max_new_tokens = T; the codec
makes 12.5 steps per second of audio, so T = 1000 is an 80 s clip) and includes decoding (clip by clip, as in
production). The text length is matched to T (Chinese reads ~4.4 characters/s). Records the peak memory allocated and
reserved by PyTorch and the time per step. Writes E:\\gc-audio\\_test\\vram\\results.json and prints a linear fit.
Run only while the worker is idle (it uses the whole GPU).
  python bench_vram.py"""
import json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tts_worker as W                                   # noqa: E402

OUT = Path("E:/gc-audio/_test/vram")
GRID = [(T, B) for T in (250, 1000, 2000, 3000) for B in (1, 4, 16, 32) if B * T <= 32000]
BASE = ("予观夫巴陵胜状，在洞庭一湖。衔远山，吞长江，浩浩汤汤，横无际涯；朝晖夕阴，气象万千。此则岳阳楼之大观也，前人之述备矣。"
        "然则北通巫峡，南极潇湘，迁客骚人，多会于此，览物之情，得无异乎？")


def main():
    import torch
    cfg = W.load_config(Path(__file__).resolve().parent / "tts_config.json")
    cfg["decode_one_by_one"] = True
    cfg["gpu_mem_fraction"] = 0.95
    OUT.mkdir(parents=True, exist_ok=True)
    model = W.load_model(cfg)
    model.generate_custom_voice(text="预热。", language="Chinese", speaker=cfg["speaker"], max_new_tokens=60)
    torch.cuda.synchronize()
    weights = torch.cuda.memory_allocated() / 2**30
    print(f"model loaded: {weights:.2f} GiB allocated", flush=True)
    rows = []
    for T, B in GRID:
        n = max(10, int(T / 12.5 * 4.4))                 # characters that take about T steps to read
        text = (BASE * (n // len(BASE) + 1))[:n]
        torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats(); torch.cuda.synchronize()
        t = time.time()
        try:
            model.generate_custom_voice(text=[text] * B, language=["Chinese"] * B, speaker=[cfg["speaker"]] * B,
                                        max_new_tokens=T, min_new_tokens=T, **W.gen_kwargs(cfg))
            torch.cuda.synchronize()
            dt = time.time() - t
            r = dict(T=T, B=B, chars=n, sec_audio=T / 12.5, peak_alloc=torch.cuda.max_memory_allocated() / 2**30,
                     peak_reserved=torch.cuda.max_memory_reserved() / 2**30, seconds=dt, ms_per_step=1000 * dt / T,
                     x_realtime=B * T / 12.5 / dt)
        except torch.OutOfMemoryError:
            r = dict(T=T, B=B, chars=n, oom=True)
            torch.cuda.empty_cache()
        rows.append(r)
        print("RUN " + json.dumps({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()}), flush=True)
        (OUT / "results.json").write_text(json.dumps(dict(weights_gib=weights, runs=rows), indent=1), encoding="utf-8")
    import numpy as np
    ok = [r for r in rows if not r.get("oom")]
    X = np.array([[1, r["B"], r["B"] * r["T"]] for r in ok], float)
    for key in ("peak_alloc", "peak_reserved"):
        y = np.array([r[key] for r in ok]); c, *_ = np.linalg.lstsq(X, y, rcond=None)
        print(f"FIT {key} GiB = {c[0]:.2f} + {c[1]:.3f}*B + {c[2] * 1000:.3f}*B*T/1000   "
              f"(max error {np.max(np.abs(X @ c - y)):.2f} GiB)", flush=True)
    X2 = np.array([[1, r["B"], r["B"] * r["T"] / 2] for r in ok], float)   # mean sequence length over the run = T/2
    y2 = np.array([r["ms_per_step"] for r in ok]); c2, *_ = np.linalg.lstsq(X2, y2, rcond=None)
    print(f"FIT ms/step = {c2[0]:.1f} + {c2[1]:.2f}*B + {c2[2] * 1000:.3f}*B*(T/2)/1000", flush=True)


if __name__ == "__main__":
    main()
