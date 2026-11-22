"""Speed of MOSS-TTS-Local-Transformer-v1.5 served by SGLang-Omni (OpenAI-compatible /v1/audio/speech): the same 32
Chinese explanation clips as bench_moss_speed.py, cloned Serena (reference + transcript), [pause 0.8s] after sentence
ends, sent with N concurrent requests. Prints audio seconds, wall time and x real time; saves the WAVs.
  python bench_sglang.py [concurrency=16] [url=http://localhost:8000]"""
import io, json, re, sys, time, wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bench_moss_speed as B                             # noqa: E402  (same texts, same pause markers)

REF_AUDIO = "/refs/serena_zh_explain.mp3"                # path inside the container
REF_TEXT = json.loads((Path(__file__).resolve().parents[1] / "refs" / "refs.json").read_text(encoding="utf-8"))["serena_zh_explain"]["text"]
OUT = Path(__file__).resolve().parents[1] / "_test" / "sglang"


def one(i, text, url):
    t = time.time()
    r = requests.post(f"{url}/v1/audio/speech", timeout=600, json={
        "model": "/models/MOSS-TTS-Local-Transformer-v1.5", "voice": "default", "input": text,
        "ref_audio": REF_AUDIO, "ref_text": REF_TEXT, "language": "Chinese", "response_format": "wav"})
    r.raise_for_status()
    (OUT / f"{i:02d}.wav").write_bytes(r.content)
    with wave.open(io.BytesIO(r.content)) as w:
        sec = w.getnframes() / w.getframerate()
    return sec, time.time() - t


def main():
    conc = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"
    OUT.mkdir(parents=True, exist_ok=True)
    items = [B.tagged(s) for s in B.texts()]
    one(99, items[0], url)                               # warm-up (reference encode, graph capture)
    t0 = time.time()
    with ThreadPoolExecutor(conc) as ex:
        res = list(ex.map(lambda a: one(a[0], a[1], url), enumerate(items)))
    wall = time.time() - t0
    audio = sum(r[0] for r in res)
    print(f"RESULT {len(items)} clips, {audio:.0f}s audio in {wall:.0f}s = {audio / wall:.2f}x real time "
          f"(concurrency {conc}); per request {min(r[1] for r in res):.0f}-{max(r[1] for r in res):.0f}s", flush=True)


if __name__ == "__main__":
    main()
