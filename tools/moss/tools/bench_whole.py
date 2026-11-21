"""Test: read a whole poem / a whole classical text in ONE clip, instead of line by line.
Same settings as production (T 0.5 / 0.5); A = no instruction, B = teaching-style instruction, 2 tries each.
Also measures, for long clips, whether the pitch drifts inside a clip (median F0 per 8-second window).
Writes E:\\gc-audio\\_test\\whole\\<n>_<try>.mp3, results.json and listen.html (the site's current line-by-line clips
played one after another, next to the 3 whole-text clips). Run only while the worker is idle.
  python bench_whole.py"""
import html, json, re, subprocess, sys, time, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tts_worker as W                                   # noqa: E402

ROOT = Path("E:/gc-audio")
OUT = ROOT / "_test" / "whole"
TRIES = 2
SETTINGS = [("A", None), ("B", "用自然、清晰、有精神的讲解语气，语速适中。")]   # A: as in production, B: teaching style
B = "https://shanchuan.org/middle/readaloud/yuwen/"
POEMS = [   # (title, author, text) - the lines the site already has are found in its transcripts
    ("望岳", "杜甫", "岱宗夫如何？齐鲁青未了。造化钟神秀，阴阳割昏晓。荡胸生曾云，决眦入归鸟。会当凌绝顶，一览众山小。"),
    ("春望", "杜甫", "国破山河在，城春草木深。感时花溅泪，恨别鸟惊心。烽火连三月，家书抵万金。白头搔更短，浑欲不胜簪。"),
    ("使至塞上", "王维", "单车欲问边，属国过居延。征蓬出汉塞，归雁入胡天。大漠孤烟直，长河落日圆。萧关逢候骑，都护在燕然。"),
    ("闻王昌龄左迁龙标遥有此寄", "李白", "杨花落尽子规啼，闻道龙标过五溪。我寄愁心与明月，随君直到夜郎西。"),
    ("黄鹤楼", "崔颢", "昔人已乘黄鹤去，此地空余黄鹤楼。黄鹤一去不复返，白云千载空悠悠。晴川历历汉阳树，芳草萋萋鹦鹉洲。"
                     "日暮乡关何处是？烟波江上使人愁。"),
    ("钱塘湖春行", "白居易", "孤山寺北贾亭西，水面初平云脚低。几处早莺争暖树，谁家新燕啄春泥。乱花渐欲迷人眼，浅草才能没马蹄。"
                        "最爱湖东行不足，绿杨阴里白沙堤。"),
    ("次北固山下", "王湾", "客路青山外，行舟绿水前。潮平两岸阔，风正一帆悬。海日生残夜，江春入旧年。乡书何处达？归雁洛阳边。"),
    ("如梦令", "李清照", "常记溪亭日暮，沉醉不知归路。兴尽晚回舟，误入藕花深处。争渡，争渡，惊起一滩鸥鹭。"),
    ("水调歌头", "苏轼", "明月几时有？把酒问青天。不知天上宫阙，今夕是何年。我欲乘风归去，又恐琼楼玉宇，高处不胜寒。"
                     "起舞弄清影，何似在人间。转朱阁，低绮户，照无眠。不应有恨，何事长向别时圆？人有悲欢离合，"
                     "月有阴晴圆缺，此事古难全。但愿人长久，千里共婵娟。"),
    ("渔家傲，秋思", "范仲淹", "塞下秋来风景异，衡阳雁去无留意。四面边声连角起，千嶂里，长烟落日孤城闭。浊酒一杯家万里，"
                          "燕然未勒归无计。羌管悠悠霜满地，人不寐，将军白发征夫泪。"),
    ("江城子，密州出猎", "苏轼", "老夫聊发少年狂，左牵黄，右擎苍，锦帽貂裘，千骑卷平冈。为报倾城随太守，亲射虎，看孙郎。"
                           "酒酣胸胆尚开张。鬓微霜，又何妨！持节云中，何日遣冯唐？会挽雕弓如满月，西北望，射天狼。"),
]
PROSE = [   # (title, author, [site clip keys of the paragraphs, in order]) - the text is the site's own
    ("小石潭记", "柳宗元", ["e572a211", "b0e6c8a0", "1cd732f1", "997efe1c", "a142cb52"]),
    ("桃花源记", "陶渊明", ["c399a1a1", "f682d512", "267e0eb4", "a79c97e2", "102e2b6b"]),
    ("岳阳楼记", "范仲淹", ["cc8eef3a", "9553c40c", "2a59d2e1", "957539d0", "3c329a3a", "fea1bc4b"]),
]
LESSONS = ("yw-tang-poems", "yw-song-ci", "yw-wenyan-classics")
PUNCT = re.compile(r"[，。？！；：、“”‘’…（）\s,.?!;:]")


def site_clips():
    out = []
    for les in LESSONS:
        t = json.loads(urllib.request.urlopen(B + les + ".json", timeout=60).read().decode("utf-8"))
        out += [dict(c, lesson=les) for c in t["clips"] if c["lang"] == "zh"]
    return out


def line_cover(text, clips):
    """the site's existing line clips that together read this poem, in order (greedy, no overlaps)"""
    norm = PUNCT.sub("", text)
    found = []
    for c in clips:
        s = PUNCT.sub("", c["send"])
        if len(s) >= 5 and s in norm:
            found.append((norm.index(s), len(s), c))
    found.sort(key=lambda x: (x[0], -x[1]))
    cover, end = [], 0
    for pos, n, c in found:
        if pos >= end:
            cover.append(c); end = pos + n
    return cover, sum(len(PUNCT.sub("", c["send"])) for c in cover), len(norm)


def f0_windows(pcm, sr, ffmpeg, win=8.0):
    """median F0 per window (Hz) - shows whether the voice drifts inside one long clip"""
    import librosa
    import numpy as np
    r = subprocess.run([ffmpeg, "-hide_banner", "-nostdin", "-loglevel", "error", "-f", "s16le", "-ar", str(sr),
                        "-ac", "1", "-i", "pipe:0", "-ar", "16000", "-c:a", "pcm_f32le", "-f", "f32le", "pipe:1"],
                       input=pcm, capture_output=True, check=True, timeout=300)
    x = np.frombuffer(r.stdout, dtype="<f4")
    f0, vo, _ = librosa.pyin(x, fmin=120, fmax=600, sr=16000, frame_length=1024)
    hop = 256 / 16000; n = int(win / hop); meds = []
    for i in range(0, len(f0), n):
        seg = f0[i:i + n][vo[i:i + n] & np.isfinite(f0[i:i + n])]
        if seg.size > 20:
            meds.append(round(float(np.median(seg)), 1))
    return meds


def main():
    cfg = W.load_config(Path(__file__).resolve().parent / "tts_config.json")
    cfg["decode_one_by_one"] = True
    cfg["gpu_mem_fraction"] = 0.9
    qa = dict(cfg["qa"], pace=dict(cfg["qa"]["pace"], zh=[3.0, 6.5]))   # the limits for poetry / classical prose
    clips = site_clips()
    by_key = {c["key"]: c for c in clips}
    items = []
    for title, author, text in POEMS:
        cover, got, total = line_cover(text, clips)
        items.append(dict(title=title, author=author, body=text, lines=cover, coverage=f"{got}/{total}"))
    for title, author, keys in PROSE:
        body = "".join(by_key[k]["send"] for k in keys)
        items.append(dict(title=title, author=author, body=body, lines=[by_key[k] for k in keys], coverage="paragraphs"))
    for i, it in enumerate(items):
        it["n"] = i; it["send"] = f"{it['title']}。{it['author']}。{it['body']}"
        print(f"{i:2d} {it['title']} {len(it['send'])} chars, site clips {len(it['lines'])} ({it['coverage']})", flush=True)
    jobs = sorted([(it, (s, ins, t)) for it in items for s, ins in SETTINGS for t in range(TRIES)],
                  key=lambda j: (j[1][0], len(j[0]["send"])))
    model = W.load_model(cfg)
    model.generate_custom_voice(text="预热。", language="Chinese", speaker=cfg["speaker"], max_new_tokens=60)
    from concurrent.futures import ProcessPoolExecutor
    pool = ProcessPoolExecutor(6)
    OUT.mkdir(parents=True, exist_ok=True)
    futs = []
    cap_n = lambda n: 16 if n <= 130 else 6 if n <= 260 else 2   # long texts in small batches (GPU memory)
    batches = []
    for name, _ in SETTINGS:                             # one setting per batch (no mixed instructions)
        cur = []
        for j in (j for j in jobs if j[1][0] == name):   # sorted short to long
            if cur and len(cur) >= cap_n(len(j[0]["send"])):
                batches.append(cur); cur = []
            cur.append(j)
        if cur:
            batches.append(cur)
    for b, part in enumerate(batches):
        b *= 16
        texts = [it["send"] for it, _ in part]
        ins = [x[1] for _, x in part]
        cap = W.batch_tokens(texts, "zh", True)
        t = time.time()
        wavs, sr = model.generate_custom_voice(text=texts, language=["Chinese"] * len(texts),
                                               speaker=[cfg["speaker"]] * len(texts), max_new_tokens=cap,
                                               **({"instruct": ins} if any(ins) else {}), **W.gen_kwargs(cfg))
        print(f"batch {b // 16 + 1}: {len(part)} clips, longest {max(map(len, texts))} chars, {time.time() - t:.0f}s",
              flush=True)
        for (it, tr), a in zip(part, wavs):
            pcm = W.pcm16(a)
            W.to_mp3(cfg, pcm, sr, OUT / f"{it['n']:02d}_{tr[0]}{tr[2] + 1}.mp3")
            sec = len(pcm) / 2 / sr
            futs.append((it, tr, sec, cap / W.CODEC_HZ,
                         pool.submit(W.check_clip_qa, pcm, sr, it["send"], "zh", qa, cfg["ffmpeg"]),
                         pool.submit(f0_windows, pcm, sr, cfg["ffmpeg"])))
    for it, tr, sec, cap_sec, q, w in futs:
        q = q.result(); w = w.result()
        it.setdefault("tries", {})[f"{tr[0]}{tr[2] + 1}"] = dict(sec=round(sec, 1), pace=round(q.pace or 0, 2), f0=round(q.f0 or 0, 1),
                                                  ok=not q.reasons, capped=sec >= cap_sec - 0.5, windows=w)
    for it in items:
        print(f"RESULT {it['title']:12s} " + "  ".join(
            f"#{k}: {v['sec']:5.1f}s {v['pace']:.2f}c/s F0 {v['f0']:.0f} win {min(v['windows'] or [0]):.0f}-"
            f"{max(v['windows'] or [0]):.0f}{' CAPPED' if v['capped'] else ''}{'' if v['ok'] else ' (gate)'}"
            for k, v in sorted(it["tries"].items())), flush=True)
    for it in items:
        it["lines"] = [dict(key=c["key"], lesson=c["lesson"], send=c["send"]) for c in it["lines"]]
    (OUT / "results.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    write_page(items)


def write_page(items):
    rows = []
    for it in items:
        srcs = [f"../../gc-audio-lang-math/yuwen/{c['lesson']}/zh/{c['key']}.mp3" for c in it["lines"]
                if (ROOT / "gc-audio-lang-math" / "yuwen" / c["lesson"] / "zh" / f"{c['key']}.mp3").exists()]
        seq = (f'<button type=button data-seq=\'{json.dumps(srcs)}\'>▶ 逐句连播（{len(srcs)} 段）</button>'
               if srcs else '<span class=m>网站上没有这首的逐句录音</span>')
        tries = "".join(
            f'<div class=try><span class=m>{"讲解语气" if k[0] == "B" else "不加指令"} {k[1]}</span> '
            f'<audio controls preload="none" src="{it["n"]:02d}_{k}.mp3"></audio>'
            f'<div class="m{"" if v["ok"] else " bad"}">{v["sec"]:.0f} 秒 · {v["pace"]:.1f} 字/秒 · 音高 {v["f0"]:.0f} Hz'
            f'（分段 {min(v["windows"] or [0]):.0f}–{max(v["windows"] or [0]):.0f}）{" · 被截断" if v["capped"] else ""}</div></div>'
            for k, v in sorted(it["tries"].items()))
        rows.append(f'<section><h2>{html.escape(it["title"])} · {html.escape(it["author"])} '
                    f'<span class=m>{len(it["send"])} 字</span></h2><p class=t>{html.escape(it["body"])}</p>'
                    f'<div class=cmp><div><div class=h>现在：逐句录音</div>{seq}</div>'
                    f'<div><div class=h>整篇一次录：不加指令 2 次，加讲解语气 2 次</div>{tries}</div></div></section>')
    page = f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>整篇朗读测试</title><style>
:root{{--bg:#fafaf7;--fg:#1d1d1b;--muted:#6b6b66;--line:#e3e2dc;--bad:#9b2c2c;--acc:#2f6f5e}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161615;--fg:#ecebe6;--muted:#9a9993;--line:#2e2d2a;--bad:#e58b8b;--acc:#7cc4ad}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 system-ui,"Microsoft YaHei",sans-serif}}
main{{max-width:1000px;margin:0 auto;padding:16px}}h1{{font-size:20px}}h2{{font-size:16px;margin:0 0 4px}}
section{{border-top:1px solid var(--line);padding:14px 0}}.t{{margin:4px 0 10px}}.m{{color:var(--muted);font-size:12px}}
.bad{{color:var(--bad)}}.h{{font-size:13px;color:var(--muted);margin-bottom:4px}}
.cmp{{display:grid;grid-template-columns:1fr 2fr;gap:16px}}@media (max-width:700px){{.cmp{{grid-template-columns:1fr}}}}
audio{{height:30px;width:100%;max-width:360px}}.try{{margin-bottom:6px}}
button{{font:inherit;padding:4px 12px;border-radius:14px;border:1px solid var(--acc);background:var(--bg);color:var(--acc);cursor:pointer}}
</style></head><body><main><h1>整篇朗读测试</h1>
<p class=m>左边：网站现在的逐句录音，按顺序连播。右边：同样的文字（加上题目、作者）一次录完：不加指令录 2 次（和正式录音相同），加“讲解语气”指令录 2 次。
红字 = 没通过质检（音高 185–300 Hz，诗文语速 3.0–6.5 字/秒）。"分段"是每 8 秒的音高中位数，范围大说明一条录音里声音在变。</p>
{"".join(rows)}</main><script>
let cur = null;
document.addEventListener('click', e => {{ const b = e.target.closest('button[data-seq]'); if (!b) return;
  if (cur) {{ cur.pause(); cur = null; }}
  const list = JSON.parse(b.dataset.seq); let i = 0;
  const next = () => {{ if (i >= list.length) return; cur = new Audio(list[i++]); cur.onended = next; cur.play(); }};
  document.querySelectorAll('audio').forEach(a => a.pause()); next(); }});
document.addEventListener('play', e => {{ if (cur && e.target !== cur) {{ cur.pause(); cur = null; }} }}, true);
</script></body></html>"""
    (OUT / "listen.html").write_text(page, encoding="utf-8")
    print(f"page: {OUT / 'listen.html'}", flush=True)


if __name__ == "__main__":
    main()
