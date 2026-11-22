#!/usr/bin/env python3
"""Genius Classroom read-aloud worker - runs on the TTS PC (Windows, Python 3.10+, ffmpeg, git, an NVIDIA GPU).

DRAFT: written on the content PC, which has no Python - so it has not been run yet. Start with the self-test in HANDOFF.md.

It downloads the lesson transcripts the site publishes (https://shanchuan.org/middle/readaloud/), records every clip with
Qwen3-TTS (voice Serena) ONE AT A TIME, saves MP3s into the audio repos (one folder per lesson), writes each lesson's
manifest.js + status, pushes, waits for GitHub Pages and checks the live files byte for byte.

  python tts_worker.py init                 write tts_config.json (edit it), check git / ffmpeg / repos
  python tts_worker.py test-voice           record two test sentences (en + zh) -> <root>/_test/*.wav, print their pace
  python tts_worker.py migrate              one-time: copy the site's current MP3s into the lesson folders (no TTS)
  python tts_worker.py run                  record lesson by lesson, push + verify each finished lesson, then exit
  python tts_worker.py run --loop           ... and keep going: check for new or changed lessons every poll_minutes
  python tts_worker.py status               print each repo's lesson labels (also in <repo>/status/STATUS.md)
Options: --lesson biology/cell-theory (only that lesson)  --fake (no model: a quiet tone of the right length, for testing)
         --no-push (commit locally only)  --config path
"""
import argparse, datetime, hashlib, json, multiprocessing as mp, os, queue, random, re, shutil, subprocess, sys, tempfile, time
import math
import urllib.error, urllib.request, wave
from collections import deque
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, wait, FIRST_COMPLETED
from contextlib import nullcontext
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_CONFIG = {
    "root": "D:/gc-audio",                       # the audio repos are cloned here: <root>/<repo name>/
    "transcripts": "https://shanchuan.org/middle/readaloud/",
    "old_audio": "https://shanchuan.org/middle/audio/",   # migrate: where the current MP3s are (<lang>/<key>.mp3)
    "model": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",     # check the name of the model you installed
    "device": "cuda:0",
    "speaker": "Serena",                         # the user chose serena for BOTH languages; no style instructions; normal speed
    "kbps": 48, "sample_rate": 24000,            # MP3, mono, 24 kHz, 48 kbps ("good enough, leaning good")
    "loudness_lufs": -16,                        # every clip normalised to this loudness (the user found it too quiet)
    "temperature": None,                         # sampling temperature of the talker / sub-talker; None = checkpoint's
    "subtalker_temperature": None,               # 0.9 (the user found 0.9 unstable for Chinese: pitch / voice drift)
    "voice_tag": "serena",                       # written to the ledger for every recording; rows with another tag
                                                 # (recorded with other settings) are recorded again: one uniform set
    "rerecord_below_kbps": 48,                   # ledger rows below this (the old server's 32 kbps serena clips, and copies
                                                 # of them) are forgotten and recorded again here: the user wants one set
    "models": 1,                                 # model processes side by side (each takes the next batch)
    "batch": 1,                                  # clips per model call (same language, similar length); 1 = one at a time
    "batch_audio_s": 300,                        # ... and at most this many seconds of padded audio per call (GPU memory)
    "qa": {"enabled": True, "f0_min": 185, "f0_max": 300, "pace": {"zh": [3.0, 7.0], "en": [8.0, 18.0]},
           "min_chars_for_pace": 8, "tries": 4, "workers": 6},
    "max_tries": 4,                              # then the clip is labelled failed and the worker moves on
    "timeout_short_s": 75,                       # a text under 40 characters that takes longer is stuck
    "timeout_per_char_s": {"en": 0.6, "zh": 2.0},   # longer texts: 180 s + this per character
    "cooldown_after_crash_s": 120,               # after a hang / CUDA error: wait, then reload the model
    "push_every": 100,                           # also push in the middle of a big lesson (e.g. _shared) every N new clips
    "poll_minutes": 30,
    "retry_failed_after_hours": 12,
    "hold": [],                                  # clips never to send, e.g. "en:39ecd1af" (hung the old server)
    "ffmpeg": "ffmpeg", "git": "git",
}
LANG_NAME = {"en": "English", "zh": "Chinese"}
HELD_LOGGED = set()                              # held lessons already reported in the log
PACE = {"en": (7.0, 22.0), "zh": (2.8, 9.0)}     # characters per second of a normal recording (outside = garbled/cut)
EST_PACE = {"en": 11.0, "zh": 4.0}               # a little slower than typical (13 / 4.8): expected length for batching
UA = {"User-Agent": "gc-readaloud-worker/1", "Cache-Control": "no-cache"}


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


LOGFILE = None                                   # <root>/worker.log (set in main): the same lines as the console
BEATFILE = None                                  # <root>/worker.heartbeat: touched by the main loop at least every
                                                 # minute; supervise.ps1 restarts a worker whose heartbeat stops


def beat():
    if BEATFILE:
        try:
            BEATFILE.write_text(now(), encoding="utf-8")
        except OSError:
            pass


def nap(seconds):
    """sleep in steps of at most 60 s, beating, so a long wait never looks like a hang"""
    end = time.time() + seconds
    while time.time() < end:
        beat(); time.sleep(min(60, max(0, end - time.time())))
    beat()


def single_instance(root):
    """only one worker may write the repos: hold a lock on <root>/worker.lock for the life of the process"""
    f = open(root / "worker.lock", "a+")
    try:
        import msvcrt
        f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
    except ImportError:
        import fcntl
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("another tts_worker is already running - exiting", flush=True); sys.exit(9)
    except OSError:
        print("another tts_worker is already running - exiting", flush=True); sys.exit(9)
    return f


def log(*a):
    line = " ".join([f"[{now()}]"] + [str(x) for x in a])
    print(line, flush=True)
    if LOGFILE:
        try:
            with open(LOGFILE, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError:
            pass


# ------------------------------------------------------------------------------------------------------------------
# Qwen3-TTS: ADAPT THESE TWO FUNCTIONS to the package you installed (read its README). They run in a child process, so
# a CUDA error or a hang only kills the child; the parent waits, reloads the model and goes on.
#  - speaker Serena, language English/Chinese, NO instruct / style text, normal speed
#  - cap the generation length if the package allows it (e.g. max_new_tokens), so a text can never generate forever
#    (on the old server the single word "mitochondria." never stopped and then the GPU crashed)
# ------------------------------------------------------------------------------------------------------------------
CODEC_HZ = 12.5                                  # Qwen3-TTS-12Hz: 12.5 codec frames (= generated tokens) per second of audio


def max_tokens(text, lang, slow=False):
    """generation cap that scales with the text: 1.5x the slowest normal pace + 3 s, at least 8 s.
    (the checkpoint default is 8192 tokens = 11 minutes - that is how "mitochondria." ran forever on the old server)
    A recording cut by the cap is slower than PACE allows, so record() rejects it and tries again."""
    sec = max(8.0, len(text) / PACE[lang][0] * 1.5 * (1.6 if slow else 1.0) + 3.0)
    return int(sec * CODEC_HZ) + 10


def load_model(cfg):
    import torch
    from qwen_tts import Qwen3TTSModel           # pip package qwen-tts 0.1.1 (github.com/QwenLM/Qwen3-TTS)
    # sdpa attention: flash-attn has no Windows wheels; the 1.7B model fits easily in 20 GB without it
    model = Qwen3TTSModel.from_pretrained(cfg["model"], device_map=cfg["device"], dtype=torch.bfloat16,
                                          attn_implementation="sdpa")
    # a hard share of GPU memory per model process: on Windows a full GPU does not fail, it silently spills into
    # system memory and gets very slow. With a cap an oversized batch fails fast ("out of memory") and is split.
    frac = cfg.get("gpu_mem_fraction") or 0.9 / max(1, int(cfg.get("models", 1)))
    torch.cuda.set_per_process_memory_fraction(float(frac), torch.device(cfg["device"]))
    # optionally turn codes into waveforms one clip at a time: decoding a whole batch at once is the memory peak of a
    # batch. model.decode_s counts the seconds spent decoding (for bench.py)
    tok = model.model.speech_tokenizer
    whole = tok.decode
    model.decode_s = 0.0
    one_by_one = cfg.get("decode_one_by_one", False)

    def decode(items, *a, **k):
        t = time.time()
        if one_by_one:
            wavs, fs = [], None
            for it in items:
                w, fs = whole([it], *a, **k)
                wavs += list(w)
        else:
            wavs, fs = whole(items, *a, **k)
        model.decode_s += time.time() - t
        return wavs, fs
    tok.decode = decode
    return model


def gen_kwargs(cfg):
    """sampling settings from the config (None = the checkpoint's default)"""
    return {k: float(cfg[k]) for k in ("temperature", "subtalker_temperature") if cfg.get(k) is not None}


def synthesize(model, cfg, text, lang):
    """Return (samples, sample_rate); samples = 1-D float array in [-1, 1] or int16."""
    # speaker Serena, explicit language, NO instruct (None = no style text), normal speed; temperature from the config
    wavs, sr = model.generate_custom_voice(
        text=text, language=LANG_NAME[lang], speaker=cfg["speaker"], max_new_tokens=max_tokens(text, lang),
        **gen_kwargs(cfg))
    return wavs[0], sr


def batch_tokens(texts, lang, slow=False):
    """cap for a whole batch: ~2x the typical length of its longest text + 2 s (normal recordings are at most ~1.5x).
    A batch runs until its slowest clip ends, so one runaway clip must not hold up 15 finished ones for long.
    A clip that reaches this cap is cut, so record_batch() never keeps it: it is recorded again on its own."""
    # slow = the batch holds poetry / classical prose (subjects in qa.slow_subjects): read slower on purpose
    sec = max(4.0, max(len(t) for t in texts) / EST_PACE[lang] * 1.7 * (1.6 if slow else 1.0) + 2.0)
    return min(int(sec * CODEC_HZ) + 10, max(max_tokens(t, lang, slow) for t in texts))


def synthesize_batch(model, cfg, texts, lang, slow=False):
    """several texts of ONE language in one call -> ([samples, ...], sample_rate). On this PC the time per step hardly
    grows with the batch (the GPU waits for the CPU), so a batch of 16 is ~10x faster than 16 single calls."""
    wavs, sr = model.generate_custom_voice(
        text=list(texts), language=[LANG_NAME[lang]] * len(texts), speaker=[cfg["speaker"]] * len(texts),
        max_new_tokens=batch_tokens(texts, lang, slow), **gen_kwargs(cfg))
    return list(wavs), sr


def pcm16(a):
    import numpy as np
    a = np.asarray(a).reshape(-1)
    if a.dtype != np.int16:
        a = (np.clip(a.astype("float32"), -1.0, 1.0) * 32767.0).astype("<i2")
    return a.astype("<i2").tobytes()


def synth_child(conn, cfg):
    is_moss = cfg.get("engine") == "moss"
    try:
        if is_moss:
            import torch
            from moss_engine import Moss

            paths = {k: cfg["moss"][k] for k in ("model", "codec", "refs") if k in cfg["moss"]}
            model = Moss(**paths, ffmpeg=cfg["ffmpeg"])
        else:
            model = load_model(cfg)
    except Exception as e:                       # noqa: BLE001
        conn.send(("dead", f"model load failed: {e!r}"))
        return
    conn.send(("ready", None))
    while True:
        msg = conn.recv()
        if msg is None:
            return
        try:
            if is_moss:
                conn.send(("ok", (model.generate(msg, cfg["ffmpeg"]), 24000)))
            else:
                text, lang, *rest = msg
                slow = bool(rest[0]) if rest else False
                if isinstance(text, list):
                    arrs, sr = synthesize_batch(model, cfg, text, lang, slow)
                    conn.send(("ok", ([pcm16(a) for a in arrs], int(sr))))
                else:
                    a, sr = synthesize(model, cfg, text, lang)
                    conn.send(("ok", (pcm16(a), int(sr))))
        except Exception as e:                   # noqa: BLE001
            msg = repr(e)
            oom = isinstance(e, torch.OutOfMemoryError) if is_moss else "out of memory" in msg.lower()
            if oom:                              # the batch was too big: free it, keep the model
                if is_moss:
                    e.__traceback__ = None      # release tensors held by the failed generation's frames
                try:
                    import torch
                    torch.cuda.empty_cache()
                except Exception:                # noqa: BLE001
                    pass
                conn.send(("oom", msg)); continue
            conn.send(("err", msg))
            if "CUDA" in msg or "cuda" in msg:
                return                           # GPU context is broken: let the parent restart us


class Hang(Exception):
    pass


class ModelLoadError(Exception):
    """the model cannot be loaded at all: stop the worker (do not label thousands of clips 'failed')"""


class PushError(Exception):
    """git push still rejected after pull --rebase: only this PC writes these repos, so stop and ask the user"""


class ChildDied(RuntimeError):
    pass


class RetryLater(RuntimeError):
    """this clip did not come out usable in its batch: try it again in a later batch"""


class GpuOOM(RuntimeError):
    """a batch did not fit in the model's share of GPU memory (the model itself is fine)"""


class Synth:
    """Serial queue: one request at a time, model kept in a child process."""

    def __init__(self, cfg, fake=False):
        self.cfg, self.fake, self.proc, self.conn = cfg, fake, None, None

    def _wait(self, timeout):
        """True = the child answered, False = timeout; a child that died (CUDA crash, segfault) raises at once
        instead of waiting out the whole timeout"""
        t0 = time.time()
        while time.time() - t0 < timeout:
            if self.conn.poll(1):
                return True
            if not self.proc.is_alive():
                code = self.proc.exitcode
                self.stop()
                raise ChildDied(f"model process died (exit code {code})")
        return False

    def _start(self):
        parent, child = mp.Pipe()
        self.proc = mp.Process(target=synth_child, args=(child, self.cfg), daemon=True)
        self.proc.start()
        self.conn = parent
        log("loading the model ...")
        try:
            ok = self._wait(900)
        except ChildDied as e:
            raise ModelLoadError(str(e)) from None
        if not ok:
            self.stop()
            raise ModelLoadError("model did not load in 15 min")
        kind, info = parent.recv()
        if kind != "ready":
            self.stop()
            raise ModelLoadError(info)
        log("model ready")

    def stop(self):
        if self.proc is not None:
            try:
                self.conn.send(None)
            except Exception:                    # noqa: BLE001
                pass
            self.proc.join(5)
            if self.proc.is_alive():
                self.proc.kill()
                self.proc.join(5)
        self.proc = self.conn = None

    def say(self, text, lang, timeout, slow=False):
        """Qwen accepts a string or list of strings. MOSS accepts a list of generation items."""
        is_moss = self.cfg.get("engine") == "moss"
        if self.fake:
            if is_moss:
                return [fake_pcm(it["text"], it["lang"]) for it in text], 24000
            return ([fake_pcm(t, lang) for t in text] if isinstance(text, list) else fake_pcm(text, lang)), 24000
        if self.proc is None or not self.proc.is_alive():
            self._start()
        self.conn.send(text if is_moss else (text, lang, slow))
        if not self._wait(timeout):
            self.stop()                          # kill the stuck child; a fresh one is started for the next clip
            raise Hang(f"no audio after {timeout:.0f} s")
        kind, data = self.conn.recv()
        if kind == "ok":
            return data
        if kind == "oom":
            raise GpuOOM(data)
        if "cuda" in str(data).lower() or not self.proc.is_alive():
            self.stop()                          # the child exits after a CUDA error: restart it (after a cooldown)
        raise RuntimeError(data)


def fake_pcm(text, lang):
    import math
    sec = max(0.6, len(text) / (14.0 if lang == "en" else 4.5))
    n = int(24000 * sec)
    return b"".join(int(800 * math.sin(i * 0.05)).to_bytes(2, "little", signed=True) for i in range(n))


# ------------------------------------------------------------------------------------------------------------------
# helpers: config, download, mp3, git
# ------------------------------------------------------------------------------------------------------------------
def load_config(path):
    cfg = dict(DEFAULT_CONFIG)
    if path.exists():
        cfg.update(json.loads(path.read_text(encoding="utf-8")))
    qa = cfg["qa"]
    defaults = DEFAULT_CONFIG["qa"]
    cfg["qa"] = {**defaults, **qa, "pace": {**defaults["pace"], **qa.get("pace", {})}}
    if cfg.get("engine") == "moss":
        cfg["moss"] = {"batch": 4, "free_tries": 3, "duration_tries": 2, **cfg.get("moss", {})}
    return cfg


def spoken(clip):
    return clip["send"]


_MOODS = {}


def load_moods(path):
    """work title -> light / neutral / somber (moods.json: a list of {work, mood, ...}, approved by the user)"""
    if path and path not in _MOODS:
        rows = json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else []
        _MOODS[path] = {r["work"]: r["mood"] for r in rows}
    return _MOODS.get(path, {})


def prepare_moss_clip(clip, *, brisk=False, moods=None):
    from moss_engine import kind_of, target_pace, with_pauses

    lid, lang = clip["_lid"], clip["lang"]
    kind = kind_of(lid, lang, clip.get("style"))
    mood = clip.get("mood") or (moods or {}).get(clip.get("work"))
    clip.update(kind=kind, pace=target_pace(lid, kind, clip["send"], mood=mood, brisk=brisk),
                text=with_pauses(spoken(clip), lang, kind))


def moss_item(clip, failed_tries, cfg):
    from moss_engine import target_tokens

    tokens = None
    if cfg["moss"]["duration_tries"] and failed_tries >= cfg["moss"]["free_tries"]:   # mood: via the pace target only
        # English has no QA pace target. Use the English rate from MOSS's length check for duration retries.
        pace = clip["pace"] if clip["pace"] is not None else 11.5
        tokens = target_tokens(clip["send"], clip["lang"], pace, clip["text"])
    return dict(text=clip["text"], lang=clip["lang"], kind=clip["kind"], tokens=tokens)


@dataclass(frozen=True)
class ClipQA:
    duration: float
    pace: float | None
    f0: float | None
    pace_ok: bool
    reasons: tuple
    score: float | None = None

    @property
    def pitch_label(self):
        return f"F0 {self.f0:.0f} Hz" if self.f0 is not None else "no voiced frames"

    @property
    def rank(self):
        if self.score is not None:
            return (self.score,)
        return not self.duration, not self.pace_ok, abs(self.f0 - 245) if self.f0 is not None else float("inf")


def check_moss_qa(clip, pcm, cfg):
    from moss_engine import check

    result = check(clip, pcm, cfg)
    return ClipQA(result["sec"], result["pace"], result["f0"] or None, True, tuple(result["reasons"]),
                  score=result["score"])


def speech_len(text, lang):
    """length used for the pace checks. In Chinese text an English word ("Mitchell 县") is spoken much faster per
    letter than per Chinese character, so each Latin letter counts 0.4 (about 2.5 letters per syllable); everything
    else counts 1 as before, which keeps the pace limits the user calibrated by listening."""
    if lang != "zh":
        # English numbers and symbols are spoken much longer than written: "56.2°S" = "fifty-six point two
        # degrees south". Count each digit as 3 letters, a decimal point between digits as 5, degree/percent as 7.
        digits = sum(ch.isdigit() for ch in text)
        points = len(re.findall(r"(?<=\d)\.(?=\d)", text))
        return len(text) + 2 * digits + 4 * points + 6 * (text.count("°") + text.count("%"))
    letters = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    return len(text) - 0.6 * letters


def check_clip_qa(pcm, sr, send, lang, qa, ffmpeg):
    """Runs in a CPU process. Resample and measure voiced F0 as in qa_check.py."""
    import librosa
    import numpy as np

    duration = len(pcm) / 2 / sr
    pace = speech_len(send, lang) / duration if duration else None
    f0 = None
    if pcm:
        resampled = subprocess.run(
            [ffmpeg, "-hide_banner", "-nostdin", "-loglevel", "error", "-threads", "1",
             "-f", "s16le", "-ar", str(sr), "-ac", "1", "-i", "pipe:0",
             "-ar", "16000", "-c:a", "pcm_f32le", "-f", "f32le", "pipe:1"],
            input=pcm, capture_output=True, check=True, timeout=120,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        samples = np.frombuffer(resampled.stdout, dtype="<f4")
        if samples.size:
            pitch, voiced, _ = librosa.pyin(samples, fmin=120, fmax=600, sr=16000, frame_length=1024)
            voiced_f0 = pitch[voiced & np.isfinite(pitch)]
            if voiced_f0.size:
                f0 = float(np.median(voiced_f0))
    reasons = []
    if f0 is None:
        reasons.append("no voiced frames")
    elif not qa["f0_min"] <= f0 <= qa["f0_max"]:
        reasons.append(f"F0 {f0:.0f} Hz outside {qa['f0_min']:g}-{qa['f0_max']:g} Hz")
    lo, hi = qa["pace"][lang]
    pace_ok = speech_len(send, lang) < qa["min_chars_for_pace"] or (pace is not None and lo <= pace <= hi)
    if not pace_ok:
        reasons.append(f"pace {pace:.1f} chars/s outside {lo:g}-{hi:g}" if pace is not None else "no audio")
    return ClipQA(duration, pace, f0, pace_ok, tuple(reasons))


def fetch(url, tries=5, *, timeout=60):
    sep = "&" if "?" in url else "?"
    for a in range(1, tries + 1):
        try:
            req = urllib.request.Request(f"{url}{sep}v={random.randint(0, 10**9)}", headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if a == tries:
                raise
        except Exception:                        # noqa: BLE001
            if a == tries:
                raise
        time.sleep(5 * a)


def probe_duration(ffprobe, path):
    result = subprocess.run(
        [str(ffprobe), "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, check=True, timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    duration = float(result.stdout)
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError(f"invalid MP3 duration for {path}: {duration}")
    return round(duration, 2)


def fp12(b):
    return hashlib.sha1(b).hexdigest()[:12]


def send_hash(send):
    return hashlib.sha1(send.encode("utf-8")).hexdigest()[:10]


def loudness_filter(cfg, wav):
    """ffmpeg filter that brings a clip to cfg["loudness_lufs"] (EBU R128 integrated loudness, true peak <= -1.5 dB).
    Two passes: measure first, then a plain gain (linear=true), so every clip ends up equally loud without changing
    its dynamics. The model's raw output is quiet (-24..-28 LUFS). None = no change (no target, or a clip too short to
    measure)."""
    target = cfg.get("loudness_lufs")
    if not target:
        return None
    r = subprocess.run([cfg["ffmpeg"], "-hide_banner", "-nostats", "-i", str(wav), "-af",
                        f"loudnorm=I={target}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        j = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
        vals = [float(j[k]) for k in ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")]
    except (ValueError, KeyError):
        return None
    if not all(v == v and abs(v) != float("inf") for v in vals):
        return None
    return (f"loudnorm=I={target}:TP=-1.5:LRA=11:measured_I={vals[0]}:measured_TP={vals[1]}:measured_LRA={vals[2]}:"
            f"measured_thresh={vals[3]}:offset={vals[4]}:linear=true")


def to_mp3(cfg, pcm, sr, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav = Path(tmp.name)
    try:
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm)
        part = dst.with_suffix(".part.mp3")
        filt = loudness_filter(cfg, wav)
        subprocess.run([cfg["ffmpeg"], "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav)]
                       + (["-af", filt] if filt else []) +
                       ["-ac", "1", "-ar", str(cfg["sample_rate"]), "-c:a", "libmp3lame", "-b:a", f"{cfg['kbps']}k",
                        str(part)], check=True)
        b = part.read_bytes()
        if len(b) < 400 or not (b[:3] == b"ID3" or (b[0] == 0xFF and (b[1] & 0xE0) == 0xE0)):
            raise RuntimeError("ffmpeg produced no MP3")
        os.replace(part, dst)
    finally:
        wav.unlink(missing_ok=True)


def git(cfg, repo, *args, check=True):
    r = subprocess.run([cfg["git"], "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip() or r.stdout.strip()}")
    return r


def push(cfg, repo, message, no_push):
    git(cfg, repo, "add", "-A")
    if not git(cfg, repo, "status", "--porcelain").stdout.strip():
        return False
    git(cfg, repo, "commit", "-q", "-m", message)
    if no_push:
        return True
    for a in range(1, 6):
        if git(cfg, repo, "push", "-q", "origin", "HEAD:main", check=False).returncode == 0:
            return True
        git(cfg, repo, "pull", "-q", "--rebase", "origin", "main", check=False)
        time.sleep(10 * a)
    raise PushError(f"push failed: {repo}")


# ------------------------------------------------------------------------------------------------------------------
# one audio repo: <root>/<name>/<subject>/<topic>/<lang>/<key>.mp3 + manifest.js, status/
# ------------------------------------------------------------------------------------------------------------------
LEDGER_HEAD = "lang\tkey\tlesson\tvoice\tkbps\tdate\tsource\tsend\n"


class Repo:
    def __init__(self, name, path, url, min_kbps=0, voice_tag=None, record_langs=LANG_NAME):
        self.name, self.path, self.url = name, Path(path), url
        self.voice_tag = voice_tag or "serena"
        self.filtered_ledger = set()              # old ledger rows still on disk until the next save
        self.status = self.path / "status"
        if not (self.path / ".git").exists():
            raise SystemExit(f"{self.path} is not a git clone - clone https://github.com/gladcolor/{name}.git there first")
        self.status.mkdir(exist_ok=True)
        marker = self.path / ".nojekyll"         # GitHub Pages must not run Jekyll (it would hide the _shared folder)
        if not marker.exists():
            marker.touch()
        # a worker killed mid-commit / mid-rebase (crash, supervisor restart) leaves git state behind: clean it up.
        # Safe: single_instance() guarantees no other worker is using these repos.
        lock = self.path / ".git" / "index.lock"
        if lock.exists():
            lock.unlink(); log(f"{name}: removed a stale .git/index.lock")
        if (self.path / ".git" / "rebase-merge").exists() or (self.path / ".git" / "rebase-apply").exists():
            subprocess.run(["git", "-C", str(self.path), "rebase", "--abort"], capture_output=True)
            log(f"{name}: aborted an unfinished rebase")
        gi = self.path / ".gitignore"            # half-written MP3s (killed during ffmpeg) are never committed
        if "*.part.mp3" not in (gi.read_text(encoding="utf-8") if gi.exists() else ""):
            with open(gi, "a", encoding="utf-8", newline="\n") as fh:
                fh.write("*.part.mp3\n")
        self.ledger = {}                         # (lesson, lang, key) -> row dict: clips recorded in serena
        lp = self.status / "ledger.tsv"
        if lp.exists():
            for line in lp.read_text(encoding="utf-8").splitlines()[1:]:
                p = line.split("\t")
                if len(p) >= 7:
                    if p[0] in record_langs and (int(p[4] or 0) < min_kbps or (voice_tag and p[3] != voice_tag)):
                        self.filtered_ledger.add((p[2], p[0], p[1])); continue
                    row = dict(zip(LEDGER_HEAD.strip().split("\t"), p))
                    row.setdefault("send", "")           # older rows have no known spoken text
                    self.ledger[(p[2], p[0], p[1])] = row
        self.failed = {}                         # (lesson, lang, key) -> (tries, error, date)
        fp = self.status / "failed.tsv"
        if fp.exists():
            for line in fp.read_text(encoding="utf-8").splitlines()[1:]:
                p = line.split("\t")
                if len(p) >= 6:
                    self.failed[(p[2], p[0], p[1])] = (p[3], p[4], p[5])
        sp = self.status / "lessons.json"
        self.lessons = json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {}
        dropped = {lid for lid, _, _ in self.filtered_ledger}
        for lid in dropped:                      # force the worker to record the forgotten clips
            if lid in self.lessons:
                self.lessons[lid]["fingerprint"] = ""; self.lessons[lid]["verified"] = ""
        if dropped:
            log(f"{name}: {len(dropped)} lesson(s) had clips from the old server or with other settings than "
                f"'{self.voice_tag}' - those clips are recorded again")

    def add_ledger(self, lesson, lang, key, kbps, source, send):
        row = {"lang": lang, "key": key, "lesson": lesson, "voice": self.voice_tag, "kbps": str(kbps), "date": now(),
               "source": source, "send": send}
        self.ledger[(lesson, lang, key)] = row
        self.failed.pop((lesson, lang, key), None)

    def save(self, *, invalidating=False):
        def save_lessons():
            path = self.status / "lessons.json"
            part = path.with_suffix(".part.json")
            part.write_text(json.dumps(self.lessons, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                            encoding="utf-8", newline="\n")
            part.replace(path)

        if invalidating:
            save_lessons()                       # a restart must see the invalid fingerprint before the rows disappear
        rows = sorted(self.ledger.values(), key=lambda r: (r["lesson"], r["lang"], r["key"]))
        (self.status / "ledger.tsv").write_text(LEDGER_HEAD + "".join(
            "\t".join(r[c] for c in LEDGER_HEAD.strip().split("\t")) + "\n" for r in rows), encoding="utf-8", newline="\n")
        (self.status / "failed.tsv").write_text("lang\tkey\tlesson\ttries\terror\tdate\n" + "".join(
            f"{k[1]}\t{k[2]}\t{k[0]}\t{v[0]}\t{v[1]}\t{v[2]}\n" for k, v in sorted(self.failed.items())),
            encoding="utf-8", newline="\n")
        if not invalidating:
            save_lessons()
        self.filtered_ledger.clear()
        lines = ["# Read-aloud status: " + self.name, "", f"Updated {now()}. Labels: finished / in progress / no audio / "
                 "failed / old voice / out of date. Clips: done = serena, old = older voice, missing = browser voice.", "",
                 "| lesson | label | done | old | missing | failed | held | updated | live check |",
                 "|---|---|---|---|---|---|---|---|---|"]
        for lid in sorted(self.lessons):
            s = self.lessons[lid]; c = s.get("counts", {})
            lines.append(f"| {lid} | {s.get('label', '')} | {c.get('done', 0)} | {c.get('old', 0)} | {c.get('missing', 0)} | "
                         f"{c.get('failed', 0)} | {c.get('held', 0)} | {s.get('updated', '')} | {s.get('verified', '')} |")
        (self.status / "STATUS.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def label_of(c, out_of_date=False):
    if out_of_date:
        return "out of date"
    if c["total"] and c["done"] == c["total"]:
        return "finished"
    if c["failed"]:
        return "failed"
    if c["missing"] and not c["done"]:
        return "no audio"
    if c["done"]:
        return "in progress"
    return "old voice"


# ------------------------------------------------------------------------------------------------------------------
# the work
# ------------------------------------------------------------------------------------------------------------------
@dataclass
class PendingClip:
    seq: int
    clip: dict
    jobs: list = field(default_factory=list)
    tries: int = 0
    best: tuple | None = None


class Worker:
    def __init__(self, cfg, args):
        self.cfg, self.args = cfg, args
        self.is_moss = cfg.get("engine") == "moss"
        self.record_langs = sorted(set(cfg.get("record_langs", LANG_NAME))) if self.is_moss else list(LANG_NAME)
        self.synths = [Synth(cfg, fake=args.fake) for _ in range(max(1, int(cfg.get("models", 1))))]
        self.synth_pool = queue.Queue()          # model threads take a free model from here
        for s_ in self.synths:
            self.synth_pool.put(s_)
        self.root = Path(cfg["root"])
        self.repos = {}
        self.hold = set(cfg.get("hold", []))
        self.new_since_push = 0
        self.sidx = None
        self.migrated_serena = {"en": set(), "zh": set()}
        self.pending = []                        # finished + pushed lessons waiting for their live check
        self.qa_pool = None
        self.durations_path = self.root / "cache" / "durations.json"
        self.durations = None
        self.durations_dirty = False

    def index(self):
        b = fetch(self.cfg["transcripts"] + "index.json")
        if b is None:
            raise SystemExit("cannot download readaloud/index.json")
        ix = json.loads(b.decode("utf-8"))
        for name, url in ix["repos"].items():
            if name not in self.repos and (self.root / name).exists():
                self.repos[name] = Repo(name, self.root / name, url, int(self.cfg.get("rerecord_below_kbps", 0)),
                                        self.cfg.get("voice_tag"), self.record_langs)
        entries = list(ix["lessons"]) + [dict(ix["shared"], en="shared clips", zh="shared clips", url="")]
        missing = sorted({e["repo"] for e in entries} - set(self.repos))
        if missing:
            raise SystemExit("clone these repos into " + str(self.root) + ": " + ", ".join(missing))
        return entries

    def apply_rerecord(self):
        """Forget requested rows across repos and return the affected lessons and clip keys."""
        path = self.root / "rerecord.txt"
        try:
            lines = path.read_text(encoding="utf-8-sig").splitlines()
        except FileNotFoundError:
            return {}
        keys = set()
        for line in lines:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            lang, _, key = line.partition(":")
            if lang in LANG_NAME and key:
                keys.add((lang, key))
            else:
                log(f"rerecord: ignored invalid entry {line!r}")
        affected, ledger_rows, failed_rows = {}, 0, 0
        for r in self.repos.values():
            ledger = {i for i in r.ledger if i[1:] in keys}
            ledger.update(i for i in r.filtered_ledger if i[1:] in keys)
            failed = {i for i in r.failed if i[1:] in keys}
            if not ledger and not failed:
                continue
            ledger_rows += len(ledger); failed_rows += len(failed)
            for lid, lang, key in ledger | failed:
                r.ledger.pop((lid, lang, key), None)
                r.failed.pop((lid, lang, key), None)
                r.lessons.setdefault(lid, {}).update(fingerprint="", verified="")
                affected.setdefault((r.name, lid), set()).add((lang, key))
            r.save(invalidating=True)
        if affected:
            self.sidx = None                      # old files remain on disk but are no longer a copy source
            self.pending = [p for p in self.pending if (p[0].name, p[1]) not in affected]
        stamp = datetime.datetime.now()
        while True:
            archived = path.with_name(f"rerecord.done-{stamp:%Y%m%d-%H%M%S}.txt")
            if not archived.exists():
                path.rename(archived)
                break
            stamp += datetime.timedelta(seconds=1)
        log(f"rerecord: dropped {ledger_rows} ledger rows and {failed_rows} failed rows in "
            f"{len(affected)} lessons; archived as {archived.name}")
        return affected

    def serena_file(self, lang, key, send):
        """a serena recording with compatible spoken text (any lesson, any repo) -> (path, kbps), or None"""
        if self.sidx is None:
            self.sidx = {}
            for r in self.repos.values():
                for (lesson, lg, k), row in r.ledger.items():
                    p = r.path / lesson / lg / f"{k}.mp3"
                    self.sidx.setdefault((lg, k), {})[p] = int(row["kbps"] or 0), row["send"]
        for p, (kb, known_send) in self.sidx.get((lang, key), {}).items():
            if (not known_send or known_send == send) and p.exists():
                return p, kb
        return None

    def add(self, repo, lesson, lang, key, kbps, source, send=""):
        repo.add_ledger(lesson, lang, key, kbps, source, send)
        if self.sidx is not None:
            p = repo.path / lesson / lang / f"{key}.mp3"
            self.sidx.setdefault((lang, key), {})[p] = int(kbps), send

    def batches(self, cs, lang):
        """clips sorted by length -> batches of at most cfg["batch"] clips AND at most cfg["batch_audio_s"] seconds of
        padded audio (clips x the longest clip's expected length), so long clips make smaller batches and GPU memory
        stays well below 20 GB. (Tested on this PC: 16 short clips ~ 8.5 GB and 5x real time; 32 clips filled the
        20 GB, Windows then spills to shared memory and it got slower.)"""
        bs = max(1, int(self.cfg.get("batch", 1))); budget = float(self.cfg.get("batch_audio_s", 300))
        out, cur = [], []
        for c in cs:
            est = len(c["send"]) / EST_PACE[lang]
            if cur and (len(cur) >= bs or (len(cur) + 1) * est > budget):
                out.append(cur); cur = []
            cur.append(c)
        return out + ([cur] if cur else [])

    def timeout_for(self, send, lang):
        return self.cfg["timeout_short_s"] if len(send) < 40 else 180 + self.cfg["timeout_per_char_s"][lang] * len(send)

    def wanted(self, c):
        """clips this pass records: languages in record_langs; texts marked "demand" (read only when a student asks
        for them on the page) only when record_demand is on - they are recorded after all the others (the user)"""
        # originals marked with "style" (verse / wenyan / prose) wait until record_styled is on (mood list and prose
        # pace approved by the user)
        return (c["lang"] in self.record_langs and (not c.get("demand") or bool(self.cfg.get("record_demand")))
                and (not c.get("style") or bool(self.cfg.get("record_styled"))))

    def clip_id(self, c):
        ident = c["lang"], c["key"], c["send"]
        return (*ident, c["_lid"]) if self.is_moss else ident

    def record_batch(self, clips, synth):
        """Generate a same-language batch. Return usable audio by clip identity, or None on GPU OOM."""
        lang = clips[0]["lang"]
        slow = any(c.get("_slow") for c in clips)
        timeout = 2 * max(self.timeout_for(c["send"], lang) for c in clips) * (1.6 if slow else 1.0)
        items = [c["_item"] if self.is_moss else c["send"] for c in clips]
        retry_label = "a later batch" if self.is_moss else "one by one"
        try:
            pcms, sr = synth.say(items, lang, timeout, slow)
            if self.is_moss and len(pcms) != len(clips):
                raise RuntimeError(f"MOSS returned {len(pcms)} items for {len(clips)} clips")
        except ModelLoadError:
            raise
        except GpuOOM:
            log(f"  GPU memory full for a batch of {len(clips)} {lang} - splitting it")
            return None
        except Hang as e:
            log(f"  HANG batch of {len(clips)} {lang}: {e}; cooling down, then {retry_label}")
            time.sleep(self.cfg["cooldown_after_crash_s"]); return {}
        except Exception as e:                        # noqa: BLE001
            log(f"  ERR batch of {len(clips)} {lang}: {str(e)[:200]}; {retry_label}")
            if synth.proc is None:
                time.sleep(self.cfg["cooldown_after_crash_s"])
            return {}
        if self.is_moss:                        # let MOSS QA judge pace and retain the best rejected audio
            return {self.clip_id(c): (pcm, sr, len(pcm) / 2 / sr) for c, pcm in zip(clips, pcms) if pcm}
        out, (lo, hi) = {}, PACE[lang]
        cap_sec = batch_tokens([c["send"] for c in clips], lang, slow) / CODEC_HZ
        for c, pcm in zip(clips, pcms):
            sec = len(pcm) / 2 / sr
            cps = speech_len(c["send"], lang) / max(sec, 0.1)
            if not self.args.fake and sec >= cap_sec - 0.5:     # cut off by the cap: never usable
                log(f"  ran to the batch cap ({sec:.1f}s, {len(c['send'])} chars, {lang}:{c['key']}) -> later batch")
            elif self.args.fake or speech_len(c["send"], lang) < 8 or lo <= cps <= hi:
                out[(c["key"], c["send"])] = (pcm, sr, sec)
            elif cps < lo and self.qa_pool is not None:
                # complete but slow (e.g. several short sentences with long pauses): the QA gate rejects it, and if
                # every try is slow the best one is kept and listed for review, instead of the lesson failing
                out[(c["key"], c["send"])] = (pcm, sr, sec)
            else:                                               # too fast: words may be missing
                log(f"  odd length {sec:.1f}s for {len(c['send'])} chars ({lang}:{c['key']}) -> later batch")
        return out

    def record(self, clip, synth):
        lang, send = clip["lang"], clip["send"]
        short = len(send) < 40
        timeout = self.timeout_for(send, lang)
        err = ""
        for a in range(1, self.cfg["max_tries"] + 1):
            text = send
            if a >= 2 and lang == "en" and short:    # same words written a little differently (a stuck model often recovers)
                cap = send[:1].upper() + send[1:]
                text = [send, cap, send.rstrip(". "), cap.rstrip(". ") + "!", cap][min(a - 1, 4)]
            try:
                pcm, sr = synth.say(text, lang, timeout)
            except ModelLoadError:
                raise
            except Hang as e:
                err = str(e); log(f"  HANG {lang}:{clip['key']} try {a}: {err}; cooling down")
                time.sleep(self.cfg["cooldown_after_crash_s"]); continue
            except Exception as e:                    # noqa: BLE001
                err = str(e)[:200]; log(f"  ERR {lang}:{clip['key']} try {a}: {err}")
                if synth.proc is None:
                    time.sleep(self.cfg["cooldown_after_crash_s"])
                continue
            sec = len(pcm) / 2 / sr
            cps = speech_len(send, lang) / max(sec, 0.1)
            lo, hi = PACE[lang]
            if len(send) >= 8 and not (lo <= cps <= hi) and a < self.cfg["max_tries"] and not self.args.fake:
                err = f"odd length {sec:.1f}s for {len(send)} chars"; log(f"  {err} -> again"); continue
            return pcm, sr, sec
        raise RuntimeError(err or "failed")

    def prep_lesson(self, e, mode):
        """everything for one lesson except the TTS: orphans, copies, migrate, which clips still need recording.
        -> a job (its chunks go to the model threads; take_results() / close_lesson() finish it), or None"""
        lid, repo = e["id"], self.repos[e["repo"]]
        # held lessons (config "hold_lessons": id prefixes) are left untouched until their reading rules are settled
        if any(lid == p or lid.startswith(p.rstrip("/") + "/") for p in self.cfg.get("hold_lessons") or ()):
            if lid not in HELD_LOGGED:
                HELD_LOGGED.add(lid); log(f"{lid}: held (config hold_lessons) - skipped")
            return None
        # the site cannot publish names starting with "_" (Jekyll): the _shared bucket's transcript is readaloud/shared.json
        b = fetch(self.cfg["transcripts"] + ("shared" if lid == "_shared" else lid) + ".json")
        if b is None or fp12(b) != e["fingerprint"]:
            log(f"{lid}: transcript not available yet (Pages still deploying?) - later"); return None
        tr = json.loads(b.decode("utf-8"))
        want = {(c["lang"], c["key"]): c for c in tr["clips"]}
        ldir = repo.path / lid
        job = {"e": e, "mode": mode, "repo": repo, "lid": lid, "want": want, "ldir": ldir,
               "st": repo.lessons.get(lid, {}), "changed": 0, "recorded": 0, "left": 0}
        for lang in self.record_langs:                    # orphans: clips of old versions of edited texts
            d = ldir / lang
            if d.exists():
                for f in d.glob("*.mp3"):
                    if (lang, f.stem) not in want:
                        f.unlink(); job["changed"] += 1
                        repo.ledger.pop((lid, lang, f.stem), None)
        todo, send_changed = [], 0
        for (lang, key), c in want.items():
            if not self.wanted(c):                        # other language, or an on-demand text not recorded yet
                continue
            c["_lid"] = lid
            if self.is_moss:
                prepare_moss_clip(c, brisk=e.get("pace") == "brisk", moods=load_moods(self.cfg["moss"].get("moods")))
            dst = ldir / lang / f"{key}.mp3"
            ident = lid, lang, key
            row = repo.ledger.get(ident)
            send = send_hash(c["send"])
            stale_send = bool(row and row["send"] and row["send"] != send)
            if stale_send:
                del repo.ledger[ident]; job["changed"] += 1
                if self.sidx is not None:                 # the old MP3 is still on disk
                    self.sidx.get((lang, key), {}).pop(dst, None)
            elif row and dst.exists():
                continue
            # The Qwen copy index has no reading context. MOSS clips can need different audio in another lesson.
            found = None if self.is_moss else self.serena_file(lang, key, send)
            if found and found[0] != dst:
                dst.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(found[0], dst)
                self.add(repo, lid, lang, key, found[1], "copy", send); job["changed"] += 1; continue
            if mode == "migrate":
                if not dst.exists():
                    old = fetch(f"{self.cfg['old_audio']}{lang}/{key}.mp3")
                    if old:
                        dst.parent.mkdir(parents=True, exist_ok=True); dst.write_bytes(old); job["changed"] += 1
                if dst.exists() and key in self.migrated_serena[lang]:
                    self.add(repo, lid, lang, key, 32, "migrate"); job["changed"] += 1
                continue
            if f"{lang}:{key}" in self.hold:
                continue
            fl = repo.failed.get((lid, lang, key))
            if fl and not self.args.retry_failed:
                age = datetime.datetime.now() - datetime.datetime.strptime(fl[2], "%Y-%m-%d %H:%M:%S")
                if age.total_seconds() < 3600 * self.cfg["retry_failed_after_hours"]:
                    continue
            todo.append(c)
            send_changed += stale_send
        if send_changed:
            log(f"{lid}: queued {send_changed} clip(s) because send text changed")
        if not self.is_moss and lid.split("/")[0] in set(self.cfg["qa"].get("slow_subjects") or ()):
            for c in todo:                              # poetry / classical prose: longer caps, slower pace allowed
                c["_slow"] = True
        job["todo"] = todo                              # recorded in batches by work_through()
        return job

    def run_chunk(self, chunk):
        """runs in a model thread: one batch (even of 1 clip) with a free model
        -> [(clip, (pcm, sr, sec) or RetryLater, note)]. A clip that ran to the cap or came out at an odd length is
        NOT re-recorded here one by one (that took 60-80 s per try at single-clip speed): work_through puts it back
        into the pool, so it is tried again inside a later full batch."""
        s = self.synth_pool.get()

        def batch_or_split(ch):
            got_ = self.record_batch(ch, s)
            if got_ is None:
                if len(ch) >= (2 if self.is_moss else 4):
                    return {**batch_or_split(ch[:len(ch) // 2]), **batch_or_split(ch[len(ch) // 2:])}
                return {}
            return got_
        try:
            t0 = time.time()
            got = batch_or_split(chunk)
            took = time.time() - t0
            out = []
            for c in chunk:
                ident = self.clip_id(c) if self.is_moss else (c["key"], c["send"])
                audio = got.get(ident)
                if audio is None:
                    reason = "no audio from MOSS" if self.is_moss else "ran to the cap, odd length or batch error"
                    out.append((c, RetryLater(reason), ""))
                else:
                    how = f"batch of {len(chunk)} took {took:.0f}s"
                    if self.is_moss:
                        how += f", target duration {'yes' if c['_item']['tokens'] is not None else 'no'}"
                    out.append((c, audio, how))
            return out
        finally:
            self.synth_pool.put(s)

    def take_results(self, ent, audio, how, qa=None):
        """Main thread: write one accepted clip into every lesson waiting for it."""
        c = ent.clip
        lang, key = c["lang"], c["key"]
        send = send_hash(c["send"])
        first = None
        for job in ent.jobs:
            repo, lid = job["repo"], job["lid"]
            dst = job["ldir"] / lang / f"{key}.mp3"
            try:
                if isinstance(audio, Exception):
                    raise audio
                pcm, sr, sec = audio
                if first is None:
                    to_mp3(self.cfg, pcm, sr, dst); first = dst
                else:
                    dst.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(first, dst)
                if qa is not None and qa.reasons:
                    self.review_clip(repo, lid, lang, key, qa, ent.tries)
                self.add(repo, lid, lang, key, self.cfg["kbps"], "tts", send)
                job["changed"] += 1; job["recorded"] += 1
                pitch = f" {qa.pitch_label}" if qa is not None else ""
                if self.is_moss:
                    pace = qa.pace if qa is not None else speech_len(c["send"], lang) / sec
                    target = f"{c['pace']:.1f}/s" if c["pace"] is not None else "natural"
                    how = f"pace {pace:.2f}/s, target {target}, tries {ent.tries}, {how}"
                log(f"  OK {lid} {lang}:{key} {len(c['send'])} chars {sec:.1f}s{pitch} ({how})")
            except Exception as ex:                      # noqa: BLE001
                tries = int((repo.failed.get((lid, lang, key)) or ("0",))[0])
                tries += ent.tries if self.is_moss else self.cfg["max_tries"]
                repo.failed[(lid, lang, key)] = (str(tries), str(ex)[:150].replace("\t", " "), now())
                log(f"  FAILED {lid} {lang}:{key}: {ex}")
            job["left"] -= 1
            self.new_since_push += 1
            if job["left"] and self.new_since_push >= self.cfg["push_every"]:   # big lesson (_shared): push now and then
                try:
                    self.finish(repo, lid, job["e"], job["want"], f"{lid}: {job['recorded']} clips so far")
                    self.new_since_push = 0
                except PushError:
                    raise
                except Exception as x:                   # noqa: BLE001
                    log(f"{lid}: ERROR {x!r} while finishing - tried again next pass")

    def review_clip(self, repo, lid, lang, key, qa, tries):
        with (self.root / "qa_review.tsv").open("a", encoding="utf-8", newline="\n") as fh:
            if fh.tell() == 0:
                fh.write("date\trepo\tlesson\tlang\tkey\tf0\tpace\treasons\ttries\n")
            f0 = f"{qa.f0:.2f}" if qa.f0 is not None else ""
            pace = f"{qa.pace:.2f}" if qa.pace is not None else ""
            fh.write(f"{now()}\t{repo.name}\t{lid}\t{lang}\t{key}\t{f0}\t{pace}\t{', '.join(qa.reasons)}\t{tries}\n")

    def close_lesson(self, job):
        e, repo, lid, st, want = job["e"], job["repo"], job["lid"], job["st"], job["want"]
        # also re-finish a lesson whose saved label is stale (its clips were recorded but the worker was restarted
        # before the lesson was closed - it would otherwise stay "in progress"/"old voice" forever)
        stale = st.get("label") not in ("finished", "failed")
        if job["changed"] or st.get("fingerprint") != e["fingerprint"] or stale or self.record_scope_changed(st):
            self.finish(repo, lid, e, want, f"{lid}: read-aloud ({job['mode']})")
        elif st.get("label") == "finished" and not st.get("verified") and not self.args.no_push:
            self.queue_verify(repo, lid, want)            # pushed earlier but the live check never passed
            self.pending[-1] = self.pending[-1][:3] + (time.time() - 40,)   # pushed long ago: look at once

    def work_through(self, entries, mode):
        """Lessons in catalog order, every model kept busy with FULL batches. Most lessons have only 10-40 clips per
        language, so the whole site is one pool: it holds the waiting clips of the next lessons (topped up to POOL clips,
        no limit on how many lessons ahead); each batch takes the oldest waiting clip plus the waiting clips closest to
        it in length. So lessons still finish in catalog order, each one as soon as its last clip is in (manifest,
        status, push, live check). Only the main thread touches files and git; model threads only generate audio.
        -> number of lesson errors"""
        if mode == "run":
            self.apply_rerecord()
        engine_cfg = self.cfg["moss"] if self.is_moss else self.cfg
        nmod, bs = len(self.synths), max(1, int(engine_cfg.get("batch", 1)))
        budget = float(self.cfg.get("batch_audio_s", 300))
        POOL = max(256, 8 * bs)                           # waiting clips to choose from: good length matches
        errors, seq = 0, 0
        inflight, checking = {}, {}                       # model batches and individual QA futures
        pool, waiting = [], {}                            # one entry per text, even while generating or checking
        catalog = {(e["repo"], e["id"]): e for e in entries if not self.args.lesson or e["id"] == self.args.lesson}
        lessons, remaining = deque(catalog), set(catalog)
        opened, selected, redo = {}, set(), set()
        qa_cfg = self.cfg["qa"]
        qa_tries_default = max(1, int(qa_cfg["tries"]))
        tries_by_subject = {k: max(1, int(v)) for k, v in (qa_cfg.get("tries_by_subject") or {}).items()}

        pace_by_subject = qa_cfg.get("pace_by_subject") or {}

        def qa_for(ent):                                  # pace limits per subject or per lesson (e.g. poetry is read slowly)
            subjects = {j["lid"].split("/")[0] for j in ent.jobs} | {j["lid"] for j in ent.jobs}
            custom = [pace_by_subject[x] for x in subjects if x in pace_by_subject]
            if not custom:
                return qa_cfg
            pace = dict(qa_cfg["pace"])
            for c in custom:                              # several lessons share the clip: take the widest limits
                for lg, (lo, hi) in c.items():
                    plo, phi = pace.get(lg, (lo, hi))
                    pace[lg] = [min(lo, plo), max(hi, phi)]
            return {**qa_cfg, "pace": pace}

        def tries_for(ent):                               # the user allows more tries for science subjects
            if self.is_moss:
                return engine_cfg["free_tries"] + engine_cfg["duration_tries"]
            return max([qa_tries_default] + [tries_by_subject.get(j["lid"].split("/")[0], qa_tries_default)
                                             for j in ent.jobs])

        def queue_clip(c, job):
            nonlocal seq
            ident = self.clip_id(c)
            ent = waiting.get(ident)
            if ent is None:
                seq += 1
                ent = waiting[ident] = PendingClip(seq, c)
                pool.append(ent)
            if not any(j is job for j in ent.jobs):
                ent.jobs.append(job)
                job["left"] += 1

        def within_limit(loc):
            return not self.args.limit or loc in selected or len(selected) < self.args.limit

        def close_ready():
            # every lesson whose last clip is in is finished now (manifest, push, live check), in catalog order among
            # those - not only from the front: one lesson with very long or retried clips must not hold back the
            # lessons after it (the user wants each lesson online as soon as it is complete)
            nonlocal errors
            while True:
                loc = next((p for p, j in opened.items() if not j["left"]), None)
                if loc is None:
                    break
                job = opened[loc]
                del opened[loc]
                try:
                    self.close_lesson(job)
                except PushError:
                    raise
                except Exception as x:                    # noqa: BLE001
                    errors += 1; log(f"{job['lid']}: ERROR {x!r} while finishing - tried again next pass")
                if mode == "run":
                    for place, keys in self.apply_rerecord().items():
                        if place in opened:
                            open_job = opened[place]
                            for lang, key in sorted(keys):
                                c = open_job["want"].get((lang, key))
                                if c is not None and self.wanted(c) and f"{lang}:{key}" not in self.hold:
                                    queue_clip(c, open_job)
                        elif place in catalog and place not in remaining and within_limit(place):
                            redo.add(place)                # its catalog turn passed: revisit after the current queue

        def prep_more():
            nonlocal errors
            if not lessons:
                lessons.extend(loc for loc in catalog if loc in redo)
                remaining.update(redo); redo.clear()
            loc = lessons.popleft()
            remaining.remove(loc)
            e = catalog[loc]
            if not within_limit(loc) or (mode == "run" and not self.needs_work(e)):
                return
            selected.add(loc)
            try:
                job = self.prep_lesson(e, mode)
                if job is None:
                    return
            except (ModelLoadError, PushError):
                raise
            except Exception as x:                        # noqa: BLE001  (network hiccup etc.: one lesson, not the loop)
                errors += 1; log(f"{e['id']}: ERROR {x!r} - skipped, tried again next pass"); return
            opened[loc] = job
            for c in job.pop("todo"):
                queue_clip(c, job)
            close_ready()

        def next_batch():
            if not pool:
                return None
            anchor = min(pool, key=lambda x: x.seq)        # the oldest waiting clip decides language and length
            lang, alen = anchor.clip["lang"], len(anchor.clip["send"])
            same = [x for x in pool if x.clip["lang"] == lang]
            same.sort(key=lambda x: (abs(len(x.clip["send"]) - alen), x.seq))
            chosen, longest = [], 0
            for x in same:
                lg = max(longest, len(x.clip["send"]))
                if len(chosen) >= bs or (len(chosen) + 1) * lg / EST_PACE[lang] > budget:
                    break
                chosen.append(x); longest = lg
            chosen = chosen or [anchor]
            ids = {x.seq for x in chosen}
            pool[:] = [x for x in pool if x.seq not in ids]
            return sorted(chosen, key=lambda x: len(x.clip["send"]))

        def settle(ent, audio, how, qa=None):
            c = ent.clip
            ident = self.clip_id(c)
            rejected = qa is not None and bool(qa.reasons)
            if rejected:
                log(f"  QA reject {ident[0]}:{ident[1]} {', '.join(qa.reasons)} (try {ent.tries}/{tries_for(ent)})")
                if ent.best is None or qa.rank < ent.best[2].rank:
                    ent.best = audio, how, qa
            if rejected or (isinstance(audio, Exception) and ent.best is not None):
                if ent.tries < tries_for(ent):
                    pool.append(ent)                       # same entry, including every lesson that still wants it
                    return
                audio, how, qa = ent.best
            waiting.pop(ident)
            self.take_results(ent, audio, how, qa)
            close_ready()

        ex = ThreadPoolExecutor(nmod)
        try:
            while True:
                while sum(1 for f in inflight if not f.running() and not f.done()) < nmod:   # one waiting batch per model
                    while (lessons or redo) and len(pool) < POOL:
                        prep_more()
                    chunk = next_batch()
                    if chunk is None:
                        break
                    if self.is_moss:
                        for ent in chunk:
                            ent.clip["_item"] = moss_item(ent.clip, ent.tries, self.cfg)
                    inflight[ex.submit(self.run_chunk, [ent.clip for ent in chunk])] = chunk
                futures = inflight.keys() | checking.keys()
                if not futures:
                    break
                beat()
                done, _ = wait(futures, timeout=60, return_when=FIRST_COMPLETED)
                for f in done & inflight.keys():
                    chunk = inflight.pop(f)
                    for ent, (c, audio, how) in zip(chunk, f.result()):
                        ent.tries += 1
                        if isinstance(audio, RetryLater):
                            if ent.tries < tries_for(ent):
                                log(f"  retry {c['lang']}:{c['key']} in a later batch (try {ent.tries}/{tries_for(ent)})")
                                pool.append(ent)
                                continue
                            detail = str(audio) if self.is_moss else "runs to the cap / odd length - check the text"
                            audio = RuntimeError(f"no usable recording after {ent.tries} tries ({detail})")
                        if self.qa_pool is not None and not isinstance(audio, Exception):
                            pcm, sr, _ = audio
                            if self.is_moss:
                                check = self.qa_pool.submit(check_moss_qa, c, pcm, self.cfg)
                            else:
                                check = self.qa_pool.submit(check_clip_qa, pcm, sr, c["send"], c["lang"],
                                                            qa_for(ent), self.cfg["ffmpeg"])
                            checking[check] = ent, audio, how
                        else:
                            settle(ent, audio, how)
                for f in done & checking.keys():
                    ent, audio, how = checking.pop(f)
                    try:
                        qa = f.result()
                    except Exception as x:                # noqa: BLE001  (a QA failure must not stop the worker)
                        log(f"  QA error {ent.clip['lang']}:{ent.clip['key']}: {x!r} - kept unchecked")
                        qa = None
                    settle(ent, audio, how, qa)
                self.check_pending()                      # one cheap look at lessons pushed earlier
        except BaseException:
            for f in inflight.keys() | checking.keys():
                f.cancel()
            for r in self.repos.values():
                r.save()                                  # keep the ledger of the clips already written
            raise
        finally:
            ex.shutdown(wait=True)
        return errors

    def write_timing(self, repo, lid, keys):
        if self.durations is None:
            try:
                cached = json.loads(self.durations_path.read_text(encoding="utf-8"))
            except (FileNotFoundError, ValueError):
                cached = {}
            self.durations = cached if isinstance(cached, dict) else {}

        ldir = repo.path / lid
        clips = {}
        missing = {}
        for lang in ("en", "zh"):
            for key in sorted(keys[lang]):
                path = ldir / lang / f"{key}.mp3"
                stat = path.stat()
                signature = [stat.st_size, stat.st_mtime_ns]
                cache_key = f"{repo.name}/{lid}/{lang}/{key}"
                clips[lang, key] = cache_key
                row = self.durations.get(cache_key)
                if not isinstance(row, list) or len(row) != 3 or row[:2] != signature:
                    missing[cache_key] = path, signature

        if missing:
            ffprobe = Path(shutil.which(self.cfg["ffmpeg"]) or self.cfg["ffmpeg"]).with_name("ffprobe.exe")
            with ThreadPoolExecutor(max_workers=8) as pool:
                jobs = {pool.submit(probe_duration, ffprobe, path): (key, signature)
                        for key, (path, signature) in missing.items()}
                pending = set(jobs)
                while pending:
                    beat()
                    _, pending = wait(pending, timeout=60)
                for job, (key, signature) in jobs.items():
                    self.durations[key] = [*signature, job.result()]
                    self.durations_dirty = True

        timing = {"lesson": lid, "en": {}, "zh": {}}
        for (lang, key), cache_key in clips.items():
            timing[lang][key] = {"dur": self.durations[cache_key][2]}
        data = ("/* read-aloud clip durations in seconds of this lesson - written by tts_worker.py */\n"
                "LabAudioTiming(" + json.dumps(timing, ensure_ascii=False) + ");\n").encode("utf-8")
        path = ldir / "timing.js"
        try:
            if path.read_bytes() == data:
                return None
        except FileNotFoundError:
            pass
        path.write_bytes(data)
        return data

    def save_durations(self):
        if self.durations_dirty:
            self.durations_path.parent.mkdir(parents=True, exist_ok=True)
            part = self.durations_path.with_suffix(".tmp")
            part.write_text(json.dumps(self.durations, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
            part.replace(self.durations_path)
            self.durations_dirty = False

    def ensure_timing(self):
        live = {}
        for repo in self.repos.values():
            changed = {}
            for manifest in sorted(repo.path.rglob("manifest.js")):
                lid = manifest.parent.relative_to(repo.path).as_posix()
                try:
                    match = re.search(r"LabAudioManifest\s*\(\s*(\{.*?\})\s*\)",
                                      manifest.read_text(encoding="utf-8"), re.DOTALL)
                    if match is None:
                        raise ValueError("manifest.js has no LabAudioManifest object")
                    obj = json.loads(match[1])
                    data = self.write_timing(repo, lid, {lang: obj[lang].split() for lang in ("en", "zh")})
                except (OSError, ValueError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as ex:
                    log(f"timing.js: {repo.name}/{lid}: {ex}")
                    continue
                if data is not None:
                    changed[f"{repo.url}{lid}/timing.js"] = data

            self.save_durations()
            if changed:
                n = len(changed)
                pushed = push(self.cfg, repo.path, f"timing.js: clip durations for {n} lessons", self.args.no_push)
                published = pushed and not self.args.no_push
                log(f"timing.js: {n} lesson(s) written in {repo.name}" + (" (pushed)" if published else ""))
                if published:
                    live.update(changed)
        if live:
            self.check_timing_live(live)

    def check_timing_live(self, expected):
        total = len(expected)
        deadline = time.monotonic() + 600
        checks = {}
        pool = ThreadPoolExecutor(max_workers=8)
        try:
            while expected and time.monotonic() < deadline:
                beat()
                next_poll = min(deadline, time.monotonic() + 60)
                for url in expected:
                    if url not in checks:
                        checks[url] = pool.submit(fetch, url, tries=1, timeout=10)
                wait(checks.values(), timeout=max(0, next_poll - time.monotonic()))
                for url, job in list(checks.items()):
                    if job.done():
                        del checks[url]
                        try:
                            if job.result() == expected[url]:
                                del expected[url]
                        except Exception:                       # a transient fetch error gets another poll
                            pass
                if expected:
                    nap(next_poll - time.monotonic())
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
        log(f"timing.js live: {total - len(expected)}/{total} match")

    def finish(self, repo, lid, e, want, message):
        ldir = repo.path / lid
        keys = {"en": [], "zh": []}
        for (lang, key) in want:
            if (ldir / lang / f"{key}.mp3").exists():
                keys[lang].append(key)
        ldir.mkdir(parents=True, exist_ok=True)
        man = {"lesson": lid, "voice": "serena", "en": " ".join(sorted(keys["en"])), "zh": " ".join(sorted(keys["zh"]))}
        (ldir / "manifest.js").write_text("/* read-aloud clips of this lesson - written by tts_worker.py */\nLabAudioManifest("
                                          + json.dumps(man, ensure_ascii=False) + ");\n", encoding="utf-8", newline="\n")
        self.write_timing(repo, lid, keys)
        self.save_durations()
        c = {"total": len(want), "done": 0, "old": 0, "missing": 0, "failed": 0, "held": 0}
        for (lang, key) in want:
            if not self.wanted(want[(lang, key)] if isinstance(want[(lang, key)], dict) else {"lang": lang}):
                c["total"] -= 1
                continue
            f = ldir / lang / f"{key}.mp3"
            if (lid, lang, key) in repo.ledger and f.exists(): c["done"] += 1
            elif (lid, lang, key) in repo.failed: c["failed"] += 1
            elif f"{lang}:{key}" in self.hold: c["held"] += 1
            elif f.exists(): c["old"] += 1
            else: c["missing"] += 1
        lab = label_of(c)
        repo.lessons[lid] = {"fingerprint": e["fingerprint"], "label": lab, "counts": c, "updated": now(),
                             "title": {"en": e.get("en", ""), "zh": e.get("zh", "")}, "page": e.get("url", ""),
                             "verified": ""}
        if self.is_moss:
            repo.lessons[lid]["record_langs"] = self.record_langs
        repo.save()
        pushed = push(self.cfg, repo.path, f"{message} - {lab} ({c['done']}/{c['total']} serena)", self.args.no_push)
        log(f"{lid}: {lab}  done {c['done']}/{c['total']}  old {c['old']}  missing {c['missing']}  failed {c['failed']}"
            + ("  (pushed)" if pushed and not self.args.no_push else ""))
        if lab == "finished" and pushed and not self.args.no_push:
            self.queue_verify(repo, lid, want)

    # live check: no waiting for GitHub Pages after each lesson (that left the GPU idle ~1 min per lesson). A pushed,
    # finished lesson is queued; between lessons the queue is checked once (cheap), at the end of a pass it is waited for.
    def queue_verify(self, repo, lid, want):
        self.pending = [p for p in self.pending if p[1] != lid] + [(repo, lid, dict(want), time.time())]

    def live_ok(self, repo, lid, want):
        """one look: do the live manifest, timing and MP3 files match the local files byte for byte?"""
        for name in ("manifest.js", "timing.js"):
            if fetch(f"{repo.url}{lid}/{name}") != (repo.path / lid / name).read_bytes():
                return False
        for (lang, key) in want:
            f = repo.path / lid / lang / f"{key}.mp3"
            if f.exists() and fetch(f"{repo.url}{lid}/{lang}/{key}.mp3") != f.read_bytes():
                return False
        return True

    def check_pending(self, wait=False):
        while self.pending:
            for item in list(self.pending):
                repo, lid, want, t = item
                if time.time() - t < 40:                  # Pages needs ~40 s at least: do not even look before
                    continue
                try:
                    ok = self.live_ok(repo, lid, want)
                except Exception as ex:                   # noqa: BLE001
                    log(f"{lid}: live check error {ex!r} - later"); ok = False
                if ok:
                    self.pending.remove(item)
                    s = repo.lessons[lid]; s["verified"] = now(); repo.save(); repo.dirty = True
                    t_ = s["title"]
                    log(f"VERIFIED {t_.get('zh', '')} / {t_.get('en', '')}  {s['page']}  ({s['counts']['done']} clips, "
                        "live files match)")
                    with open(self.root / "published.log", "a", encoding="utf-8") as fh:
                        fh.write(f"{now()}\t{lid}\t{s['page']}\t{s['counts']['done']}\n")
                elif time.time() - t > 25 * 60:
                    self.pending.remove(item)
                    log(f"NOT VERIFIED {lid}: live files still differ after 25 min (Pages slow?) - checked again next pass")
            if not wait or not self.pending:
                break
            beat(); time.sleep(20)
        for r in self.repos.values():                     # the "verified" marks go into the next commit; at the end
            if wait and getattr(r, "dirty", False):       # of a pass push them so STATUS.md on GitHub is current
                push(self.cfg, r.path, "live checks ok", self.args.no_push); r.dirty = False

    def record_scope_changed(self, st):
        return self.is_moss and st.get("record_langs") != self.record_langs

    def needs_work(self, e):
        st = self.repos[e["repo"]].lessons.get(e["id"])
        if any(p[1] == e["id"] for p in self.pending):
            return False                                  # pushed this pass, live check still waiting for Pages
        return (not st or self.record_scope_changed(st) or st.get("fingerprint") != e["fingerprint"] or st.get("label") != "finished"
                or not st.get("verified"))

    def run(self, mode):
        qa = self.cfg["qa"]
        pool = ProcessPoolExecutor(max_workers=int(qa["workers"]), mp_context=mp.get_context("spawn")) \
            if mode == "run" and qa["enabled"] and not self.args.fake else nullcontext()
        try:
            with pool as self.qa_pool:
                self.run_passes(mode)
        finally:
            for s_ in self.synths:
                s_.stop()

    def run_passes(self, mode):
        backfill_timing = mode == "run"
        while True:
            try:
                entries = self.index()
            except Exception as ex:                       # noqa: BLE001
                if not self.args.loop or mode == "migrate":
                    raise
                log(f"cannot read readaloud/index.json ({ex!r}) - next try in 5 min"); nap(300); continue
            if backfill_timing:
                self.ensure_timing()
                backfill_timing = False
            if mode == "migrate":
                self.migrated_serena = {l: set((fetch(f"{self.cfg['transcripts']}migrate/serena_{l}.txt") or b"")
                                               .decode("utf-8").split()) for l in ("en", "zh")}
            errors = self.work_through(entries, mode)
            self.check_pending(wait=True)                 # end of the pass: wait for the remaining live checks
            if errors:
                log(f"{errors} lesson(s) hit an error this pass" + (" - run migrate again to finish them"
                                                                    if mode == "migrate" else ""))
            if not self.args.loop or mode == "migrate":
                break
            log(f"all lessons checked - next check in {self.cfg['poll_minutes']} min")
            nap(60 * self.cfg["poll_minutes"])


def main():
    for s in (sys.stdout, sys.stderr):               # Windows console is cp1252/gbk: Chinese titles would crash print()
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:                            # noqa: BLE001
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["init", "test-voice", "migrate", "run", "status"])
    ap.add_argument("--config", default=str(HERE / "tts_config.json"))
    ap.add_argument("--lesson", default="")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--fake", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--retry-failed", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="at most this many lessons per pass (for testing)")
    args = ap.parse_args()
    cpath = Path(args.config)
    cfg = load_config(cpath)
    global LOGFILE, BEATFILE
    if args.command in ("run", "migrate") and Path(cfg["root"]).exists():
        _lock = single_instance(Path(cfg["root"]))  # noqa: F841  (held until the process ends)
        LOGFILE = Path(cfg["root"]) / "worker.log"
        BEATFILE = Path(cfg["root"]) / "worker.heartbeat"
        beat()
    if args.command == "init":
        if not cpath.exists():
            cpath.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n", encoding="utf-8")
            print(f"wrote {cpath} - edit root / model / device, then run init again")
        for tool in (cfg["git"], cfg["ffmpeg"]):
            print(f"{tool}: {'ok' if shutil.which(tool) else 'NOT FOUND'}")
        ix = json.loads(fetch(cfg["transcripts"] + "index.json").decode("utf-8"))
        for name in ix["repos"]:
            p = Path(cfg["root"]) / name
            print(f"{name}: {'cloned at ' + str(p) if (p / '.git').exists() else 'MISSING - git clone https://github.com/gladcolor/' + name + '.git ' + str(p)}")
        print(f"transcripts: {len(ix['lessons'])} lessons + {ix['shared']['clips']} shared clips (generated {ix['generated']})")
        return
    if args.command == "test-voice":
        s = Synth(cfg, fake=args.fake)
        out = Path(cfg["root"]) / "_test"; out.mkdir(parents=True, exist_ok=True)
        for lang, text in (("en", "Diffusion moves molecules from high to low concentration, and it needs no energy."),
                           ("zh", "长安是唐朝的都城，丝绸之路从这里出发。")):
            t0 = time.time()
            if cfg.get("engine") == "moss":
                clip = {"_lid": "", "lang": lang, "send": text}
                prepare_moss_clip(clip)
                (pcm,), sr = s.say([moss_item(clip, 0, cfg)], lang, 300)
                if not pcm:
                    raise RuntimeError(f"MOSS returned no audio for {lang}")
            else:
                pcm, sr = s.say(text, lang, 300)
            sec = len(pcm) / 2 / sr
            with wave.open(str(out / f"test_{lang}.wav"), "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm)
            lo, hi = PACE[lang]; cps = len(text) / sec
            print(f"{lang}: {sec:.1f}s audio at {sr} Hz in {time.time() - t0:.1f}s, {cps:.1f} chars/s "
                  f"({'normal' if lo <= cps <= hi else 'ODD'}) -> {out / f'test_{lang}.wav'}")
        s.stop(); return
    w = Worker(cfg, args)
    if args.command == "status":
        w.index()
        for r in w.repos.values():
            labels = {}
            for s in r.lessons.values():
                labels[s["label"]] = labels.get(s["label"], 0) + 1
            print(f"{r.name}: " + ", ".join(f"{k} {v}" for k, v in sorted(labels.items())) + f"  -> {r.path / 'status' / 'STATUS.md'}")
        return
    w.run(args.command)


if __name__ == "__main__":
    mp.freeze_support()
    main()
