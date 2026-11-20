# TTS PC → content PC (mailbox)

The two machines talk only through their repos:
- **TTS PC → content PC:** this file (and the files it links), in `gladcolor/gc-audio-science`. Newest first.
- **content PC → TTS PC:** write `FOR-TTS-PC.md` in **this repo** (`gladcolor/gc-audio-science`, root), newest first,
  dated. nshanchuan and ningshanchuan are invited as collaborators (write) on all three audio repos, so you can push
  it directly. (`tools/readaloud/FOR-TTS-PC.md` in `ningshanchuan/middle` is read too.) Please change only
  `FOR-TTS-PC.md` here: the audio, manifests and `status/` are written by the TTS PC's worker.

Older messages (all answered or done) are in [archive/FOR-CONTENT-PC-2026-11.md](archive/FOR-CONTENT-PC-2026-11.md).

## Open

### 2026-11-20 14:50: mailbox tidied
- The user asked to keep the mailbox files small. This file now holds only the open items, a short "waiting on the
  content PC" list, status and done; the answered messages moved, unchanged, to
  [archive/FOR-CONTENT-PC-2026-11.md](archive/FOR-CONTENT-PC-2026-11.md).
- Please do the same with `FOR-TTS-PC.md` when convenient (for example `archive/FOR-TTS-PC-2026-11.md` in this repo):
  keep the messages I have not answered yet, move the rest.

### 2026-11-20 14:35: full scan of all transcripts - 87 classes, 3 export bugs, and a layered plan for the spoken script
At the user's request, Codex (on the TTS PC) scanned every `send` (9,725 clips) for anything a TTS model is likely
to read wrongly or badly. Results in this repo:
- [textscan/textscan_report.md](textscan/textscan_report.md): 87 classes ranked by impact; for each a detection rule,
  counts per language, real examples, how a narrator should read it, and **fixed rule** or **needs context**
  (LLM rewrite + review), with false-positive notes.
- [textscan/textscan.py](textscan/textscan.py): the scanner; it reads `transcripts/*.json` next to it (copies of
  `readaloud/<lesson>.json`, `/` in the id replaced by `__`). The TTS PC will re-run it after each publish.

**Please fix first - errors made by the current export (`Prep`), verified by hand:**
1. **Multi-digit exponents broken** (4 clips): 10²⁶ became "10 的平方 ⁶" / "10 squared ⁶", 2¹²⁸ became "2¹ 的平方 ⁸"
   (astronomy/big-bang e4cae1fa, a07c0cd8; cs/cs-data-crypto 6401a64e, 095aafc6). Should be 10的26次方, 2的128次方.
2. **Reaction arrows turned into commas** (8 clips): "二氧化碳 + 水 —（光能），有机物（葡萄糖）+ 氧气",
   "H⁺ + OH⁻，H2O", "酸 + 碱，盐 + 水", "HCl + NaOH，NaCl + H2O" (biology/food-webs, chemistry/acids-bases,
   chemistry/reactions). The direction is lost; read 生成 / "gives" (e.g. 在光能作用下，二氧化碳和水生成葡萄糖和氧气).
3. **Double bond read as an equation**: "O 等于 O 键" (chemistry/reactions 305a540e) should be 氧氧双键 / O=O 双键.

**Largest classes** (clips zh / en): term cards split by full stops 734 / 1,888; over the length limit (150 zh /
400 en characters) 614 / 369 - these risk the model stopping part-way; years and dates 1,131 / 1,042; acronyms
487 / 942; degrees and coordinates 660 / 754; decimals 923 / 933; Chinese-English mixing 1,000 / 224; middle dot
1,020 / 6; `+` between words 368 / 330; UTC offsets, polyphonic characters (536 zh), units, percent, ranges, etc.

**Suggested layers for the spoken script** (the user asked the TTS PC to look for existing solutions too):
1. **Standard text normalization with an established library** instead of adding rules one by one: numbers, dates,
   times, temperatures (-10°C → 零下十度), percentages, fractions, units. Open-source options used by Chinese TTS
   projects: PaddleSpeech `zh_normalization` (Apache 2.0, plain Python regexes; also used by GPT-SoVITS, ChatTTS) and
   WeTextProcessing (WeNet; used with CosyVoice).
2. **Math from the LaTeX source**, not from the flattened text: absolute value, powers, roots, fractions, inequalities,
   reactions. The DAISY MathCAT speech rules (with Chinese rule files) show the conventions.
3. **Context classes by LLM rewrite + your review** (the override table): `+` and `/` between words, term cards,
   eye-only content, splitting texts over the length limit at sentence groups.
4. **TTS PC check after each publish** (textscan.py) and feedback here.

### 2026-11-20 14:20: PR #3 fixes the 容易混淆 repetition (please merge or replace); requests from the user
- **PR https://github.com/ningshanchuan/middle/pull/3** (3 lines in `shared/lab.js`, for the 13:40 bug): the user asked
  for a quick fix because the pages are hard to use now (also math/exponents). In `Lab.mixFor()`, when the box's card
  holds a step player (`.ma-narration .ma-step`), the box is read only when the last step (`n/n`) is shown. Tested on
  math/exponents?lang=zh with auto-read and auto-play: steps 1-10, then the mix-up box once. Please merge it, or put
  the same logic into your current `lab.js` if you are editing that file, so nothing is lost.
- **Request 1 - read the "记忆小窍门" boxes too.** They are `div.memory` with `<b>记忆小窍门</b>` (e.g. math/equations:
  "怎么包上的，就倒着拆开…"). `mixFor` reads only `.mix`, so these are never read. The user wants them read like the
  mix-up box (after the card's text; in a step player after the last step), and recorded (the crawler captures them).
- **Request 2 - read scattered text on demand.** For text without a 🔊 button:
  - **hover:** after a short hover, show a small 🔊 next to the text; clicking it reads that text;
  - **double-click** on ordinary text could also read it;
  - **quiz options and other clickable items: hover only.** A double-click there would choose an answer, so it must
    not be used; the 🔊 must also not trigger the option's own click.
  - Notes from the TTS PC: touch screens have no hover (a long press could show the 🔊); double-click normally selects
    a word, so reading on double-click should not break copying text; texts read this way should be captured by the
    crawler so they get recordings (otherwise the browser voice reads them).

### 2026-11-20 13:55: symbols still not read (send lint); the spoken script can start now
- **From the user:** on https://shanchuan.org/middle/math/integers.html?lang=zh the narration does not read symbols such
  as the absolute value bars ("|a| 等于 |负a|"). The user asks for the preprocessing (the spoken-script step) we agreed.
- **Send lint (TTS PC, read only, all 9,725 Chinese clips):** [SEND-LINT.md](SEND-LINT.md) in this repo: the symbols
  left in `send`, how many clips and lessons, one example each and a suggested reading. Main items: `+` between words
  (370 clips), `/` (87), `-` as a negative sign before a number (77, e.g. "太阳高度 -34 度"), `|a|` (math/integers),
  `____` blanks, `A*`. The middle dot is mostly in names (fine) but is also used as a list separator.
- **Text layout - result of the pause tests: do not add line breaks or blank lines** to `send`. They lengthen the pause
  at 。 a little, but 2-3 of 8 clips then stopped reading part-way. Instructions and temperature did not lengthen the
  pauses either. So the spoken script can be written now with ordinary punctuation; there is nothing to wait for on
  the layout. (The TTS PC is still testing model-side ways to get the ~0.8 s pause at 。 the user wants; that will not
  change how the script is written.)

### 2026-11-20 13:40: bug from the user - the 容易混淆 box is read after every animation step
**Report.** https://shanchuan.org/middle/math/negative-operations.html?lang=zh: in the animated lesson, "⚠️ 容易混淆"
is read again after each step's narration. The user: it should be read **once, after the whole animation**.

**Reproduced** (headless Chrome, auto-read on, 🔊 on in the step player, ▶): step 1 narration at 3.9 s, then the mix-up
text at 17.8 s; step 2 narration at 42.0 s, then the mix-up text again at 61.3 s; and so on.

**Cause:** `Lab.mixFor()` in `lab.js` finds the box's card with
`box.closest('.info,.card,.panel,.box,.detail,.sidebar') || box.parentElement`. On this page the `.mix` box has no card
around it, so the "card" is `section#lesson`, which also holds `.ma-narration`. Every step's narration is shown in that
section, its first phrase is found there, and the mix-up text is appended to every step.

**Suggested fix:** inside a mathanim step player, read the mix-up box only after the narration of the **last** step
(for example: `mixFor` returns '' when the card contains `.ma-player`, and mathanim's last step, or the end of
autoplay, speaks the mix-up box once). Other pages with a `.mix` box next to a step player and no card around it
have the same problem.

**Test:** the TTS PC has a small script that logs every `Lab.speak()` text with its time while a step player runs
(`tools/test_autoread.py` on the TTS PC); I will run it on this page after your fix and report.

## Waiting on the content PC (acknowledged, in progress)
- Whole-poem / whole-paragraph units for 语文, at most ~150 characters per clip (10:50 and 12:50, archived).
- Spoken-script step (朗读稿): rules / library + Codex rewrites for detected candidates + your review (11:05, 13:55,
  14:35). No line breaks in `send`.
- The 2.5 s pause after a narration in the page players of your audit (11:50, archived).
- User requests 3 (aesthetics in every subject) and 5 (more read-aloud audio), from 08:15 (archived).
- PR #2 (HANDOFF.md, documentation only): please tell me if anything in it is wrong.

## Status (what the TTS PC is doing)
- All 230 lessons and the shared clips are recorded on the TTS PC with one setting (Qwen3-TTS 1.7B CustomVoice, voice
  Serena, temperature 0.5, -16 LUFS, MP3 48 kbps) and verified live. Only new or changed clips are recorded now.
- Every new clip passes an automatic check before it is kept (pitch 185-300 Hz; pace 3.5-6.5 Chinese characters/s,
  3.0-6.5 for poetry and 文言文 lessons, 8-18 for English); failures are generated again (5 tries, 15 for science).
- Every lesson folder has `manifest.js` and `timing.js` (clip durations), rewritten whenever a lesson is finished.
- Tests in progress: how to get a pause of about 0.8 s at 。 and after the title and the author (the user's target);
  the model itself does not do it reliably. Results will come here.

## Done
- 2026-11-20: pause / resume bar and auto-read / auto-play switches live; `Lab.whenSpoken()` and the 2.5 s / 1 s
  auto-advance rule live (mathanim, lab.js auto-play); China map fetched without referrer (no more 403).
- 2026-11-20: `timing.js` with clip durations in every lesson folder; clip length limit (~150 Chinese / ~400 English
  characters) adopted in the Codex briefs; the spoken-script plan agreed.
- 2026-11-20 09:56: first full pass finished - all 230 lessons and the shared clips (9,725 clips) recorded with the new settings and verified live. From now on only new or changed clips are recorded.
- 2026-11-20 07:42: china/terrain finished and verified live (35 clips; manifest lists fe45a00d, c8432bac gone).
- 2026-11-20: fractions, doubled full stops and china/terrain fixed at the source (4d538d7).
- 2026-11-19: symbols in `send` fixed at the source (ce0c033); PR #1 closed as superseded.
- 2026-11-19: migration finished; the site switched to the audio repos ([SITE-SWITCH.md](SITE-SWITCH.md)).
