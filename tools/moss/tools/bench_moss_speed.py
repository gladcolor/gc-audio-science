"""Speed of MOSS-TTS-Local-Transformer-v1.5 on this machine (Windows or WSL), one pass, no QA: 32 Chinese explanation
clips from biology/cell-theory and china/ming-qing, cloned Serena, [pause 0.8s] after sentence ends, batches of at most
8 clips and 180 s of expected audio (as in production). Prints audio seconds, wall time and x real time.
  python bench_moss_speed.py <model dir> <codec dir> <reference mp3> [sdpa|flash_attention_2]"""
import json, re, sys, time, urllib.request

import numpy as np
import soundfile as sf
import torch

SITE = "https://shanchuan.org/middle/readaloud/"
GEN = dict(max_new_tokens=4096, do_sample=True, audio_temperature=1.7, audio_top_p=0.8, audio_top_k=25,
           audio_repetition_penalty=1.0)


def texts(n=32):
    out = []
    for lesson in ("biology/cell-theory", "china/ming-qing"):
        t = json.loads(urllib.request.urlopen(SITE + lesson + ".json", timeout=60).read().decode("utf-8"))
        out += [c["send"] for c in t["clips"] if c["lang"] == "zh" and len(c["send"]) >= 30]
    out = sorted(out, key=len)
    step = max(1, len(out) // n)
    return out[::step][:n]


def tagged(s):
    return re.sub(r"([。！？])(?=\s*\S)", lambda m: m.group(1) + "[pause 0.8s]", s)


def expected(s):
    return len(re.sub(r"\[pause [\d.]+s\]", "", s)) / 3.8 + 0.8 * s.count("[pause")


def main():
    from transformers import AutoModel, AutoProcessor
    model_dir, codec_dir, ref = sys.argv[1:4]
    attn = sys.argv[4] if len(sys.argv) > 4 else "sdpa"
    torch.backends.cuda.enable_cudnn_sdp(False)
    t = time.time()
    proc = AutoProcessor.from_pretrained(model_dir, trust_remote_code=True, codec_path=codec_dir)
    proc.audio_tokenizer = proc.audio_tokenizer.to("cuda")
    model = AutoModel.from_pretrained(model_dir, trust_remote_code=True, attn_implementation=attn,
                                      dtype=torch.bfloat16).to("cuda").eval()
    print(f"loaded in {time.time() - t:.0f}s, attention {attn}", flush=True)
    wav, sr = sf.read(ref, dtype="float32")
    if wav.ndim > 1:
        wav = wav.mean(axis=1)
    ref_codes = proc.encode_audios_from_wav([torch.from_numpy(wav)], sr)[0]
    items = [tagged(s) for s in texts()]
    batches, cur, tot = [], [], 0.0
    for s in sorted(items, key=len):
        e = expected(s)
        if cur and (len(cur) >= 8 or tot + e > 180):
            batches.append(cur); cur, tot = [], 0.0
        cur.append(s); tot += e
    batches.append(cur)
    audio_s = 0.0; t0 = time.time()
    for b in batches:
        convs = [[proc.build_user_message(text=s, language="Chinese", reference=[ref_codes])] for s in b]
        batch = proc(convs, mode="generation")
        cap = int(max(2 * expected(s) + 10 for s in b) * 12.5) + 25
        tb = time.time()
        with torch.no_grad():
            out = model.generate(input_ids=batch["input_ids"].to("cuda"), attention_mask=batch["attention_mask"].to("cuda"),
                                 **dict(GEN, max_new_tokens=min(4096, cap)))
        msgs = proc.decode(out)
        sec = sum(m.audio_codes_list[0].shape[-1] / proc.model_config.sampling_rate for m in msgs if m is not None)
        audio_s += sec
        print(f"batch of {len(b)}: {sec:.0f}s audio in {time.time() - tb:.0f}s "
              f"(peak {torch.cuda.max_memory_allocated() / 2**30:.1f} GiB)", flush=True)
    wall = time.time() - t0
    print(f"RESULT {len(items)} clips, {audio_s:.0f}s audio in {wall:.0f}s = {audio_s / wall:.2f}x real time ({attn})", flush=True)


if __name__ == "__main__":
    main()
