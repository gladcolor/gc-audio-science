"""Longer pauses at sentence ends in a recorded clip, without generating it again.
1. find the silences in the audio (20 ms frames, energy well below the speech level, at least 80 ms long);
2. match them in order to the punctuation of the text (dynamic programming on the estimated time of each mark, from
   the character position; a mark may have no pause and a pause may have no mark);
3. make every pause matched to 。！？ (and the title / author breaks) at least `major` seconds long, and pauses at
   ，、；： at least `minor`; the extra time is digital silence inserted in the middle of the pause.
  python pause_fix.py <text> <in.mp3> <out.mp3> [major=0.7] [minor=0]      (a function apply() for other scripts)"""
import subprocess, sys
from pathlib import Path

import numpy as np

SR = 24000
FFMPEG = r"<HOME>\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe"
MAJOR = set("。！？!?")
MINOR = set("，、；：,;:")


def decode(path, ffmpeg=None):
    r = subprocess.run([ffmpeg or FFMPEG, "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "pipe:1"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype="<f4").copy()


def encode(x, path, ffmpeg=None, kbps=48):
    subprocess.run([ffmpeg or FFMPEG, "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "pipe:0",
                    "-c:a", "libmp3lame", "-b:a", f"{kbps}k", str(path)], input=x.astype("<f4").tobytes(), check=True)


def silences(x, frame=0.02, min_len=0.08):
    n = int(SR * frame); k = len(x) // n
    db = 20 * np.log10(np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(1)) + 1e-9)
    speech = np.percentile(db, 90)
    quiet = db < speech - 30
    out, i = [], 0
    while i < k:
        if quiet[i]:
            j = i
            while j < k and quiet[j]:
                j += 1
            if (j - i) * frame >= min_len:
                out.append((i * frame, j * frame))
            i = j
        else:
            i += 1
    voiced = np.where(~quiet)[0]
    return out, (voiced[0] * frame if len(voiced) else 0), ((voiced[-1] + 1) * frame if len(voiced) else len(x) / SR)


def marks(text):
    """(position in spoken characters, kind) for each punctuation run"""
    out, pos, prev = [], 0.0, None
    for ch in text:
        kind = "major" if ch in MAJOR else "minor" if ch in MINOR else None
        if kind:
            if prev is not None and out and out[-1][0] == pos:   # 。” or ？！ : one mark, the stronger kind
                if kind == "major":
                    out[-1] = (pos, "major")
            else:
                out.append((pos, kind))
            prev = kind
        elif ch.strip() and ch not in "“”‘’《》（）()\"'":
            pos += 0.4 if (ch.isascii() and ch.isalpha()) else 1.0
            prev = None
    return out, pos


def match(sil, mk, total, t0, t1, miss_mark=1.2, extra_pause=0.6):
    """monotonic alignment of pauses (inside the speech) to marks; returns {pause index: mark index}"""
    sil = [(a, b) for a, b in sil if a > t0 and b < t1]
    est = [t0 + (p / total) * (t1 - t0) for p, _ in mk]
    mid = [(a + b) / 2 for a, b in sil]
    P, M = len(sil), len(mk)
    INF = 1e18
    D = np.full((P + 1, M + 1), INF); D[0, :] = np.arange(M + 1) * miss_mark; D[:, 0] = np.arange(P + 1) * extra_pause
    B = np.zeros((P + 1, M + 1), dtype=int)
    for i in range(1, P + 1):
        for j in range(1, M + 1):
            c = (D[i - 1, j - 1] + abs(mid[i - 1] - est[j - 1]), D[i - 1, j] + extra_pause, D[i, j - 1] + miss_mark)
            B[i, j] = int(np.argmin(c)); D[i, j] = c[B[i, j]]
    pairs, i, j = {}, P, M
    while i > 0 and j > 0:
        if B[i, j] == 0:
            pairs[i - 1] = j - 1; i -= 1; j -= 1
        elif B[i, j] == 1:
            i -= 1
        else:
            j -= 1
    return sil, pairs


def apply(text, x, major=0.7, minor=0.0):
    sil, t0, t1 = silences(x)
    mk, total = marks(text)
    sil, pairs = match(sil, mk, total, t0, t1)
    stats = {"major": [], "minor": [], "unmatched_pauses": len(sil) - len(pairs), "marks": len(mk)}
    inserts = []
    for i, (a, b) in enumerate(sil):
        if i not in pairs:
            continue
        kind = mk[pairs[i]][1]; stats[kind].append(round(b - a, 2))
        want = major if kind == "major" else minor
        if b - a < want:
            inserts.append((int((a + b) / 2 * SR), int((want - (b - a)) * SR)))
    # a sentence end with no pause at all: insert at the quietest 10 ms within 0.25 s of its estimated time
    done = set(pairs.values()); stats["inserted_without_pause"] = 0
    if major > 0:
        n10 = SR // 100
        e = np.sqrt(np.convolve(x ** 2, np.ones(n10) / n10, mode="same"))
        for j, (pos, kind) in enumerate(mk):
            if kind != "major" or j in done or j == len(mk) - 1:
                continue
            t = t0 + pos / total * (t1 - t0)
            lo, hi = int(max(t0, t - 0.25) * SR), int(min(t1, t + 0.25) * SR)
            if hi - lo < n10:
                continue
            at = lo + int(np.argmin(e[lo:hi:n10 // 2]) * (n10 // 2))
            inserts.append((at, int(major * SR))); stats["inserted_without_pause"] += 1
    inserts.sort()
    parts, last = [], 0
    for at, n in inserts:
        parts += [x[last:at], np.zeros(n, dtype=x.dtype)]; last = at
    parts.append(x[last:])
    return np.concatenate(parts), stats


if __name__ == "__main__":
    text, src, dst = sys.argv[1], sys.argv[2], sys.argv[3]
    major = float(sys.argv[4]) if len(sys.argv) > 4 else 0.7
    minor = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
    y, st = apply(text, decode(src), major, minor)
    encode(y, dst)
    print(st)
