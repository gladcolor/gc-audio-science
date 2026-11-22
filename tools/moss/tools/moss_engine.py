"""MOSS-TTS-Local-Transformer-v1.5 engine with the reading rules the user set (2026-11-20), and a test recorder for a
few lessons. Runs in E:\\gc-audio\\venv-moss.

Rules
- voice: Serena, cloned from fixed reference recordings in E:\\gc-audio\\refs (poem / Chinese explanation / English)
- pause markers: poems: 1.0 s after the title and the author (whole-poem units "题目。作者。正文"), 0.8 s after each
  sentence end; explanations (zh and en): 0.8 s after each sentence end; never after the last sentence
- kind from the clip's "style" field: verse / wenyan -> poem, prose -> prose (白话 literary originals), none -> explanation
- pace (characters/s over the whole clip, pauses included): short poems 2.5, long texts 3.0, prose 3.5 (proposed),
  light +0.2, somber -0.2 (mood per work, moods.json); Chinese explanations 4.0, science 3.8, everyday life 4.1;
  English: no target
- generation: first without a target duration; the check below; failures are generated again; after FREE_TRIES
  misses the clip gets a target duration (97 % of the target) for DURATION_TRIES more tries; the best try is kept
- check: pitch 175-300 Hz; pace within ±0.3 of the target (poems 2.2-2.8 for short poems); no stray sound after the
  last pause; length not over 2x the expected length

  E:\\gc-audio\\venv-moss\\Scripts\\python.exe moss_engine.py <lesson> [<lesson> ...] [--lang zh]"""
import html, json, re, subprocess, sys, time, urllib.request
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tts_worker as W                                   # noqa: E402  (mp3 encoding, pitch check, speech_len)

ROOT = Path("E:/gc-audio")
MODEL = ROOT / "models" / "MOSS-TTS-Local-Transformer-v1.5"
CODEC = ROOT / "models" / "MOSS-Audio-Tokenizer-v2"
REFS = ROOT / "refs"
SITE = "https://shanchuan.org/middle/readaloud/"
GEN = dict(max_new_tokens=4096, do_sample=True, audio_temperature=1.7, audio_top_p=0.8, audio_top_k=25,
           audio_repetition_penalty=1.0)
FREE_TRIES, DURATION_TRIES, BATCH = 5, 0, 8          # no target durations: the best free try is kept (the user);
                                                     # BATCH = most clips per batch; BUDGET_S limits long ones
BUDGET_S = 180                                       # sum of expected seconds per batch (keeps GPU memory < ~18 GB)
DEFAULT_PACE = {"poem": 2.5, "prose": 3.5, "explain": 3.8, "en": 11.5}
PROSE_PACE = 3.5                                     # 白话 literary originals (proposed; awaiting the user's approval)
MOOD_SHIFT = {"light": 0.2, "somber": -0.2}
REF_KIND = {"prose": "explain"}                      # reference recording per kind (prose: the narration reference)
SCIENCE = {"math", "physics", "chemistry", "biology", "earth", "astronomy", "cs"}
F0 = (175, 300)


# ---------------------------------------------------------------- rules
def kind_of(lesson, lang, style=None):
    """reading kind from the clip's transcript field "style" (content PC, 2026-11-21): verse / wenyan -> poem,
    prose -> prose; no field -> explanation"""
    if lang == "en":
        return "en"
    if style in ("verse", "wenyan"):
        return "poem"
    return "prose" if style == "prose" else "explain"


def target_pace(lesson, kind, send, mood=None, brisk=False):
    if kind == "en":
        return None
    if kind == "poem":
        p = 3.0 if W.speech_len(send, "zh") > 100 else 2.5
        return p + MOOD_SHIFT.get(mood or "", 0.0)
    if kind == "prose":
        return PROSE_PACE + MOOD_SHIFT.get(mood or "", 0.0)
    if brisk:
        return 4.1
    return 3.8 if lesson.split("/")[0] in SCIENCE else 4.0


def pace_window(kind, pace):
    if pace is None:
        return None
    return (pace - 0.5, pace + 0.5)                      # target ±0.5 (the user, 2026-11-20): natural variation passes


def with_pauses(send, lang, kind):
    if lang == "zh":
        text = re.sub(r"([。！？])(?=\s*\S)", lambda m: m.group(1) + "[pause 0.8s]", send)
        if kind == "poem":                               # whole-poem unit: 题目。作者。正文 -> 1 s after title / author
            m = re.match(r"^([^。！？，]{1,16})。\[pause 0\.8s\]([^。！？，]{1,6})。\[pause 0\.8s\]", text)
            if m and len(send) > len(m.group(1)) + len(m.group(2)) + 8:
                text = f"{m.group(1)}。[pause 1.0s]{m.group(2)}。[pause 1.0s]" + text[m.end():]
        return text
    return re.sub(r"((?<!\d)[.!?])(?=\s+[A-Z\"“(])", lambda m: m.group(1) + "[pause 0.8s]", send)


def expected_seconds(text, lang, kind, pace=None):
    """expected length of a clip from its (tagged) text: the words at the target pace + the pause markers"""
    words = re.sub(r"\[pause [\d.]+s\]", "", text)
    return W.speech_len(words, lang) / (pace or DEFAULT_PACE[kind]) + tags_seconds(text)


def batches(clips, budget=BUDGET_S, most=BATCH):
    """consecutive groups of (length-sorted) clips whose expected seconds sum to <= budget, at most `most` per group"""
    out, cur, tot = [], [], 0.0
    for c in clips:
        e = expected_seconds(c["text"], c["lang"], c["kind"], c.get("pace"))
        if cur and (len(cur) >= most or tot + e > budget):
            out.append(cur); cur, tot = [], 0.0
        cur.append(c); tot += e
    if cur:
        out.append(cur)
    return out


def tags_seconds(text):
    return sum(float(x) for x in re.findall(r"\[pause ([\d.]+)s\]", text))


def target_tokens(send, lang, pace, text, share=0.97):
    sec = max(W.speech_len(send, lang) / pace, tags_seconds(text) + W.speech_len(send, lang) / 6.0)
    return int(round(sec * share * 12.5))


def stray_end(x, sr=24000, frame=0.02, last_text=""):
    """True when the clip ends with a short isolated sound after a pause ('hou', a breath): <= 0.6 s after >= 0.5 s.
    Skipped when the last sentence itself is very short (a real word may follow a pause marker)."""
    if 0 < len(last_text.strip("。！？.!? ")) <= 3:
        return False
    n = int(sr * frame); k = len(x) // n
    if k < 10:
        return False
    db = 20 * np.log10(np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(1)) + 1e-9)
    idx = np.where(db > np.percentile(db, 90) - 30)[0]
    if len(idx) < 2:
        return False
    segs, s = [], idx[0]
    for a, b in zip(idx[:-1], idx[1:]):
        if b - a > 10:
            segs.append((s, a)); s = b
    segs.append((s, idx[-1]))
    if len(segs) < 2:
        return False
    dur = (segs[-1][1] - segs[-1][0] + 1) * frame
    gap = (segs[-1][0] - segs[-2][1]) * frame
    return dur <= 0.6 and gap >= 0.5


def check(clip, pcm, cfg):
    x = np.frombuffer(pcm, dtype="<i2").astype("float32") / 32768
    sec = len(x) / 24000
    lang, kind, pace_t = clip["lang"], clip["kind"], clip["pace"]
    sl = W.speech_len(clip["send"], lang)
    pace = sl / sec if sec else 0
    f0_min, f0_max = cfg.get("moss", {}).get("f0", F0)
    q = W.check_clip_qa(pcm, 24000, clip["send"], lang, dict(cfg["qa"], f0_min=f0_min, f0_max=f0_max,
                                                            pace={"zh": [0, 99], "en": [0, 99]}), cfg["ffmpeg"])
    reasons = [r for r in q.reasons if r.startswith("F0") or r.startswith("no ")]
    win = pace_window(kind, pace_t)
    if win and sl >= 15 and not (win[0] <= pace <= win[1]):
        reasons.append(f"pace {pace:.2f} outside {win[0]:.1f}-{win[1]:.1f}")
    expected = sl / (pace_t or (11.5 if lang == "en" else 4.0)) + tags_seconds(clip["text"])
    if sec > 2 * expected + 3:
        reasons.append(f"too long ({sec:.0f}s, expected ~{expected:.0f}s)")
    last = re.split(r"\[pause [\d.]+s\]", clip["text"])[-1]
    if stray_end(x, last_text=last):
        reasons.append("stray sound at the end")
    score = abs(pace - pace_t) / pace_t if pace_t else 0.0
    return dict(sec=round(sec, 1), pace=round(pace, 2), f0=round(q.f0 or 0), reasons=reasons,
                score=score + 10 * len(reasons))


# ---------------------------------------------------------------- engine
class Moss:
    def __init__(self, *, model=MODEL, codec=CODEC, refs=REFS, ffmpeg=None):
        import torch
        from transformers import AutoModel, AutoProcessor
        self.torch = torch
        torch.backends.cuda.enable_cudnn_sdp(False)
        self.proc = AutoProcessor.from_pretrained(str(model), trust_remote_code=True, codec_path=str(codec))
        self.proc.audio_tokenizer = self.proc.audio_tokenizer.to("cuda")
        self.model = AutoModel.from_pretrained(str(model), trust_remote_code=True, attn_implementation="sdpa",
                                               dtype=torch.bfloat16).to("cuda").eval()
        self.sr = int(self.proc.model_config.sampling_rate)
        ref_files = {"poem": "serena_zh_poem.mp3", "explain": "serena_zh_explain.mp3", "en": "serena_en_explain.mp3"}
        if ffmpeg is None:
            ffmpeg = W.load_config(Path(__file__).resolve().parent / "tts_config.json")["ffmpeg"]
        self.refs = {kind: self._encode(Path(refs) / name, ffmpeg) for kind, name in ref_files.items()}

    def _encode(self, path, ffmpeg):
        r = subprocess.run([ffmpeg, "-v", "error", "-i", str(path), "-ac", "1", "-ar", "24000", "-f", "f32le", "pipe:1"],
                           capture_output=True, check=True)
        wav = self.torch.from_numpy(np.frombuffer(r.stdout, dtype="<f4").copy())
        return self.proc.encode_audios_from_wav([wav], 24000)[0]

    def generate(self, items, ffmpeg):
        """items: dicts with text, lang, kind, tokens (or None) -> list of 24 kHz mono 16-bit PCM bytes (None = failed)"""
        torch = self.torch
        convs = [[self.proc.build_user_message(text=it["text"], language="Chinese" if it["lang"] == "zh" else "English",
                                               reference=[self.refs[REF_KIND.get(it["kind"], it["kind"])]],
                                               **({"tokens": it["tokens"]} if it.get("tokens") else {}))] for it in items]
        batch = self.proc(convs, mode="generation")
        # cap the batch at 2x the longest expected clip + 10 s (a clip that does not stop no longer holds the whole
        # batch for 4096 frames = 5.5 min); a target duration is honoured as given
        secs = [it["tokens"] / 12.5 + 5 if it.get("tokens") else
                2 * expected_seconds(it["text"], it["lang"], it["kind"], it.get("pace")) + 10 for it in items]
        gen = dict(GEN, max_new_tokens=min(GEN["max_new_tokens"], int(max(secs) * 12.5) + 25))
        with torch.no_grad():
            out = self.model.generate(input_ids=batch["input_ids"].to("cuda"),
                                      attention_mask=batch["attention_mask"].to("cuda"), **gen)
        pcms = []
        for m in self.proc.decode(out):
            if m is None:
                pcms.append(None); continue
            wav = m.audio_codes_list[0].float().mean(dim=0).cpu().numpy()          # 48 kHz stereo -> mono
            r = subprocess.run([ffmpeg, "-v", "error", "-f", "f32le", "-ar", str(self.sr), "-ac", "1", "-i", "pipe:0",
                                "-ar", "24000", "-f", "s16le", "pipe:1"], input=wav.astype("<f4").tobytes(),
                               capture_output=True)
            pcms.append(r.stdout if r.returncode == 0 and r.stdout else None)
        return pcms


def record(engine, clips, cfg, log=print, on_best=None):
    """clips: dicts with lesson, lang, key, send, kind, pace, text. Adds best pcm + metrics + tries to each clip;
    on_best(clip) is called whenever a clip gets a better recording (so results are saved as they come)."""
    todo = list(clips)
    for rnd in range(1, FREE_TRIES + DURATION_TRIES + 1):
        if not todo:
            break
        use_dur = rnd > FREE_TRIES
        todo.sort(key=lambda c: len(c["text"]))
        left = []
        for part in batches(todo):
            for c in part:
                c["tokens"] = target_tokens(c["send"], c["lang"], c["pace"], c["text"]) if use_dur and c["pace"] else None
            t = time.time()
            pcms = engine.generate(part, cfg["ffmpeg"])
            log(f"round {rnd}{' (target duration)' if use_dur else ''}: {len(part)} clips in {time.time() - t:.0f}s")
            for c, pcm in zip(part, pcms):
                c["tries"] = c.get("tries", 0) + 1
                m = check(c, pcm, cfg) if pcm else dict(sec=0, pace=0, f0=0, reasons=["no audio"], score=99)
                if pcm and (c.get("best") is None or m["score"] < c["best"]["score"]):
                    c["best"] = dict(m, pcm=pcm, round=rnd, duration=bool(c["tokens"]))
                    if on_best:
                        on_best(c)
                log(f"  {c['lesson']} {c['lang']}:{c['key']} try {c['tries']}: {m['sec']}s {m['pace']}/s F0 {m['f0']}"
                    f" {'OK' if not m['reasons'] else '; '.join(m['reasons'])}")
                if m["reasons"]:
                    left.append(c)
        todo = left
    return clips


# ---------------------------------------------------------------- test recorder
def lesson_clips(lesson, lang):
    for wait in (0, 60, 120, 240):                       # Pages answers 404/503 for a few minutes while it redeploys
        time.sleep(wait)
        try:
            raw = W.fetch(SITE + lesson + ".json")
        except Exception:                                # noqa: BLE001
            raw = None
        if raw:
            break
    t = json.loads(raw.decode("utf-8"))
    out = []
    for c in t["clips"]:
        if c["lang"] != lang:
            continue
        kind = kind_of(lesson, lang, c.get("style"))
        out.append(dict(lesson=lesson, lang=lang, key=c["key"], send=c["send"], kind=kind,
                        pace=target_pace(lesson, kind, c["send"]), text=with_pauses(c["send"], lang, kind)))
    return t, out


def main():
    lang = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else "zh"
    args = [a for i, a in enumerate(sys.argv[1:], 1) if not (a.startswith("--") or sys.argv[i - 1] == "--lang")]
    lessons = [a for a in args if "/" in a]
    cfg = W.load_config(Path(__file__).resolve().parent / "tts_config.json")
    out = ROOT / "_test" / "lessons"
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    engine = Moss()
    print(f"model loaded in {time.time() - t0:.0f}s", flush=True)
    idx = json.loads(W.fetch(SITE + "index.json").decode("utf-8"))
    repo_of = {l["id"]: l["repo"] for l in idx["lessons"]}
    titles, allclips = {}, []
    for l in lessons:
        t, clips = lesson_clips(l, lang)
        titles[l] = t.get("title", {}).get("zh") if isinstance(t.get("title"), dict) else t.get("title")
        allclips += clips
    print(f"{len(allclips)} clips in {len(lessons)} lessons", flush=True)
    t1 = time.time()
    def save(c):                                         # write the best recording so far at once
        d = out / c["lesson"].replace("/", "__") / lang
        d.mkdir(parents=True, exist_ok=True)
        W.to_mp3(cfg, c["best"]["pcm"], 24000, d / f"{c['key']}.mp3")
    record(engine, allclips, cfg, log=lambda s: print(s, flush=True), on_best=save)
    audio_s = 0.0
    for c in allclips:
        d = out / c["lesson"].replace("/", "__") / lang
        d.mkdir(parents=True, exist_ok=True)
        if c.get("best"):
            W.to_mp3(cfg, c["best"]["pcm"], 24000, d / f"{c['key']}.mp3")
            audio_s += c["best"]["sec"]
    wall = time.time() - t1
    bad = [c for c in allclips if not c.get("best") or c["best"]["reasons"]]
    print(f"RESULT {len(allclips)} clips, {audio_s / 60:.1f} min audio in {wall / 60:.1f} min ({audio_s / wall:.1f}x real time), "
          f"tries {sum(c.get('tries', 0) for c in allclips)}, target duration used {sum(1 for c in allclips if c.get('best', {}).get('duration'))}, "
          f"still failing {len(bad)}", flush=True)
    rows = []
    for l in lessons:
        cs = [c for c in allclips if c["lesson"] == l]
        items = []
        for c in cs:
            b = c.get("best") or {}
            old = ROOT / repo_of.get(l, "") / l / lang / f"{c['key']}.mp3"
            oldtag = f'<div class=m>现在的 Qwen</div><audio controls preload="none" src="../../{old.relative_to(ROOT).as_posix()}"></audio>' if old.exists() else '<div class=m>（网站上还没有这句的录音：新句子）</div>'
            items.append(f'<div class=row><p class=t>{html.escape(c["send"])}</p><div class=pair><div><div class=m>MOSS · {b.get("sec", 0):.0f} 秒 · '
                         f'{b.get("pace", 0):.2f} 字/秒（目标 {c["pace"] or "自然"}）· 试了 {c.get("tries", 0)} 次{" · 用了目标时长" if b.get("duration") else ""}'
                         f'{" · 仍未通过：" + "；".join(b.get("reasons", [])) if b.get("reasons") else ""}</div>'
                         f'<audio controls preload="none" src="{l.replace("/", "__")}/{lang}/{c["key"]}.mp3"></audio></div><div>{oldtag}</div></div></div>')
        rows.append(f'<section><h2>{html.escape(str(titles[l]))} <span class=m>{l} · {len(cs)} 句</span></h2>{"".join(items)}</section>')
    page = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MOSS 三课试录</title><style>
:root{{--bg:#fafaf7;--fg:#1d1d1b;--muted:#6b6b66;--line:#e3e2dc}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161615;--fg:#ecebe6;--muted:#9a9993;--line:#2e2d2a}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 system-ui,"Microsoft YaHei",sans-serif}}
main{{max-width:1000px;margin:0 auto;padding:16px}}h1{{font-size:20px}}h2{{font-size:17px;margin:18px 0 6px}}
.row{{border-top:1px solid var(--line);padding:8px 0}}.t{{margin:2px 0 6px}}.m{{color:var(--muted);font-size:12px}}
.pair{{display:flex;flex-wrap:wrap;gap:16px}}audio{{height:30px;width:300px}}
</style></head><body><main><h1>MOSS-TTS 三课试录（中文）</h1>
<p class=m>按正式规则录制：克隆 Serena，句末停顿 0.8 秒，按学科的目标语速，先自然生成、不合格再重录，必要时用目标时长。
右边是网站现在的 Qwen 录音，供对比。</p>{"".join(rows)}</main></body></html>"""
    (out / "listen.html").write_text(page, encoding="utf-8")
    print(f"page: {out / 'listen.html'}", flush=True)


if __name__ == "__main__":
    main()
