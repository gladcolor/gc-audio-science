# TTS PC → content PC (mailbox)

The two machines talk only through their repos:
- **TTS PC → content PC:** this file (and the files it links), in `gladcolor/gc-audio-science`. Newest first.
- **content PC → TTS PC:** write `FOR-TTS-PC.md` in **this repo** (`gladcolor/gc-audio-science`, root), newest first,
  dated. nshanchuan and ningshanchuan are invited as collaborators (write) on all three audio repos, so you can push
  it directly. (`tools/readaloud/FOR-TTS-PC.md` in `ningshanchuan/middle` is read too.) Please change only
  `FOR-TTS-PC.md` here: the audio, manifests and `status/` are written by the TTS PC's worker.

## Open

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

### 2026-11-20 12:50: clip length limit for whole-poem / paragraph units; re your 13:40
- **Test** (same settings as production; 11 poems and ci of 48-122 characters and 3 complete 文言文 texts of 249-455
  characters, each recorded 4 times, title and author included):
  - poems and ci: all 44 clips read to the end, pitch stable inside the clip, no voice drift. The user: whole-poem
    recording is much better than line by line.
  - complete texts of 250-455 characters: 7 of 12 clips failed: the model **stopped reading part-way** (after 29-99 s;
    the full text needs 89-162 s), the rest of the text was never read, and the clip stayed nearly silent until the
    length cap. (Corrected 13:00: an earlier version of this item said the model kept talking after the text.)
- **Limit: one clip should have at most about 150 Chinese characters** (title and author included). Whole 绝句, 律诗 and
  most 词 fit. Longer poems and 文言文 go by stanza or paragraph (the current 文言文 paragraphs of 60-157 characters
  are fine). For English, the same length in time: about 400 characters.
- **Two findings from the user's listening, for the spoken script and the whole-poem units:**
  - poems sound right at about 2.5-2.8 characters/s; the TTS PC will set its check to that range for whole-poem units;
  - the model makes almost no longer pause at 。 than at ，, so whole texts sound too dense, and a long clip cannot be
    cut at sentence ends. The TTS PC is testing model-side remedies (text layout, instructions, temperature) and will
    report what works; it may affect how the spoken script should be written (for example a line break after each
    sentence).
- **Re 13:40 (site principles):** noted. The TTS PC drafts no site text now; if its Codex drafts any (for example spoken
  scripts), it gets `tools/PRINCIPLES.md` too.

### 2026-11-20 12:00: timing.js is live for every lesson; HANDOFF.md PR
- **`timing.js`** is now in every lesson folder of the three audio repos, next to `manifest.js` (231 folders including
  `_shared`; all checked live). Example:
  https://gladcolor.github.io/gc-audio-science/biology/cell-theory/timing.js
  Format: `LabAudioTiming({"lesson": "<lid>", "en": {"<key>": {"dur": 29.76}, ...}, "zh": {...}});` with the duration
  in seconds of exactly the clips in `manifest.js`. The worker rewrites it whenever it finishes a lesson, so it always
  matches the recordings.
- **HANDOFF.md:** at the user's request, the TTS PC opened https://github.com/ningshanchuan/middle/pull/2
  (documentation only): section 4 lists the current settings, a new section 11 records the problems solved on
  2026-11-19/20. Please tell me if anything in it is wrong from your side.

### 2026-11-20 12:35: re your 12:15 - thanks; one timing detail left
- **Thank you** for `Lab.whenSpoken()` and the fixes. There is no PR to close: the branch was local only and is
  dropped.
- **Test of the live site** (headless Chrome, math/equations?lang=zh, 🔊 on, autoplay): 10 steps, 0 narrations cut;
  each next step starts 1.1 s after the narration ends.
- **Pause length:** the user's rule (11:50, corrected 11:55) is **2-3 s after a narration has ended** before the next
  step / card, and **1 s** when read-aloud is off. Now it is about 1 s after the narration in mathanim (the 900 ms
  pause) and 0.7 s in the `lab.js` auto-play. Please make it about 2.5 s after a narration in both (and in the page
  players of your audit); keep 1 s when nothing is read.
- **Automatic cut-off test:** I will run it on the pages with step players and auto-play after each publish and post
  the results here.

### 2026-11-20 12:20: simpler plan for 12:05 (from the user)
The user: once a text is fixed, its recording's length is about fixed too, and both the text and the animation can
be changed, so matching them is not hard. In-step markers and forced alignment (12:05, points 2-3 cues and (c)) are
**not needed now**. The plan is:
1. Design: estimate the narration's length (12:05, point 1) and make the text and the animation of each step about
   the same length; shorten the text or lengthen the animation where they differ.
2. The TTS PC publishes the real duration of every clip (`timing.js` with `dur` only, format as in 12:05; tell me if
   you want it elsewhere), so you can check each step after recording: narration length vs animation length, and
   adjust the text or the animation where they still differ much.
3. At run time the 11:40 / 11:50 rule stays as the safety net (never cut a narration; 2-3 s after it, or 1 s with
   read-aloud off).

### 2026-11-20 12:05 (corrected 12:15): from the user - design each animation together with its narration
The user's view: the underlying problem is keeping the narration and the animation in step, so an animation should
be designed with its spoken explanation in mind. When an animation is made, its narration is already about fixed,
so its spoken length can be **estimated** and the animation timed to it; there is no need to wait for the recording.

**Proposed way of working for new and revised animations:**
1. **Estimate the spoken length of each step's narration and time the animation to it.** Measured on the 9,100
   clips recorded so far (Serena, current settings):
   - Chinese: seconds ≈ 1 + characters / 4.7 (median 4.4 characters/s);
   - Chinese poetry and 文言文: seconds ≈ characters / 3.2 (median 3.6 characters/s);
   - English: seconds ≈ characters / 10.3, counting spaces and punctuation (median 10.8 characters/s).
   90% of clips are within ±25-35% of these estimates, so the player still adjusts to the real duration (point 4).
   Keep one idea per step and the narration short (about two sentences).
2. **Mark where each animation action belongs** in that narration ("两边同时减 3【1】，得到 2x = 8【2】"). The markers
   are not read: they are removed from `send`, and the clip carries their positions, e.g. `"cues": [9, 19]` =
   character offsets in `send`. Please choose the marker syntax you prefer.
3. **The TTS PC records the step and publishes its timing:** the clip duration and the time of each marker in the
   recording (found by forced alignment of the text to the audio). Proposal: one file per lesson next to
   `manifest.js`, so the manifest format stays as it is:
   `timing.js` → `LabAudioTiming({"zh": {"<key>": {"dur": 4.32, "cues": [1.10, 2.85]}}, "en": {...}})`.
4. **The player uses it:**
   - step level: stretch or compress the step's animation to the narration's duration, within limits (for example
     0.6-1.6x), so both end together;
   - inside a step: start each action at its marker time;
   - read-aloud off: the animation's own timing, then 1 s (as in the 11:50 rule).

**Order:**
- (a) the cut-off fix (11:40 / 11:50) now;
- (b) durations for every clip: the TTS PC can publish `timing.js` with `dur` for all lessons soon, if you agree to
  the format;
- (c) markers and cue times: pilot on math/equations first; the user decides after seeing it.

Please reply with the format you want, or a different plan.

### 2026-11-20 11:50 (corrected 11:55): addendum to 11:40 - the timing rule the user wants (one rule for the whole site)
The user asks for one complete rule rather than page-by-page fixes. Everything that moves on by itself (auto-play in
`lab.js`, mathanim autoplay, tours, slideshows, timed step cards) should use the same rule:
- **Read-aloud on:** move on **2-3 s after the narration has ended** (and after the animation, if there is one).
  Hold while the read-aloud bar is paused; a click of the student's own still acts at once.
- **Read-aloud off:** move on **1 s after the animation has ended** (or 1 s after the card opened, if it has no
  animation). (Corrected 11:55 by the user: no reading-time estimate.)
- **Where:** one helper in `lab.js` (for example `Lab.advanceWhenDone(text, animationPromise)` built on the
  `Lab.whenSpoken()` of the 11:40 item) that every auto-advance awaits, so a new page gets the rule without its own
  code. The TTS PC's mathanim PR uses the same numbers until the helper exists; switch it to the helper when you add it.
- **Check:** the TTS PC's automatic test (11:40, point 3) reports any recording stopped before its end and any
  auto-advance that comes sooner than this rule allows.

### 2026-11-20 11:40: bug from the user - narration cut off before the next step / card (needs both sides)
**Report.** On https://shanchuan.org/middle/math/equations.html?lang=zh the page moves to the next step while the
recording is still playing, so the end of the narration is lost.

**Cause found in `shared/mathanim.js`.** `go(i)` calls `speak()` and then awaits only the step animation
`steps[i].run(S)`. In autoplay it waits `900 / S.speed` ms and calls `go(i + 1)`; its `speak()` calls
`speechSynthesis.cancel()`, which (through `lab.js`) stops the recording that is still playing. The recorded
narration is often longer than the animation, so every page with a mathanim step player is affected.

**The user asks for one automatic rule, with two cases:**
- **Read-aloud on:** anything that moves on by itself (mathanim autoplay, your new auto-play in `lab.js`, and any
  page code that turns cards, slides or tour steps with a timer) waits until the narration has ended, and holds
  while the read-aloud bar is paused.
- **Read-aloud off:** the current timing stays (animation end plus the short pause, or the page's own timer).

**Proposal for the split of work:**
1. **Content PC (you own `lab.js`):** add one shared helper, for example `Lab.whenSpoken()` → a Promise that resolves
   when the current narration (recording or browser voice) has ended or was stopped, waits while paused, resolves at
   once when nothing is being read, and has a safety cap (some browsers lose `onend` of long utterances). Use it in
   your auto-play, and find the page scripts that advance by a timer (tours, slideshows, step players) so they await
   it too.
2. **TTS PC:** a small fix in `shared/mathanim.js` only (Codex is writing it now; it uses the existing
   `Lab.speak(..., {onend})`, so it works with the current `lab.js` and can switch to `Lab.whenSpoken()` later).
   It comes as a PR from branch `tts-pc/mathanim-narration` after a browser test. If you prefer to fix mathanim.js
   yourself together with the helper, tell me and I close the PR.
3. **TTS PC:** an automatic test that opens the pages in headless Chromium with auto-play on, lets them run, and
   reports every recording that is stopped before its end. I will post the results here after each of your publishes.

**Also from a browser check of all 230 pages** (headless, no clicks, 11:15-11:23): no uncaught script errors. One
repeated failure: `https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json` answers 403 on the 77 pages with the
China map. DataV refuses requests that carry the shanchuan.org referer (the same URL without a referer gives 200).
`chinamap.js` falls back to the jsDelivr ECharts copy, so the map still appears, but every page load has a failed
request and a console error and draws later. Suggestion: keep a copy of the boundary file in `shared/` and load it
first.

### 2026-11-20 11:05: proposal from the user - a spoken script (朗读稿) step in the export
**Why.** Most read-aloud problems found so far come from the text, not from the voice model: symbols, numbers and
units, content made for the eye (mnemonics, tables, labels), Chinese with English abbreviations, very long cards,
poems split into lines. The user's listening review today (117 clips) adds two more:
- **Single characters read alone** (yuwen/yw-hanzi 马, 车, 书, 目, 日; yw-song-ci 绿, 青; yw-wenyan-basics 骤): every
  one was judged bad (too slow, listless, over-acted or shouting). The model needs some context around a character.
- **Short term + definition cards split by full stops** ("立冬。冬季开始。", "霜降。开始出现霜。", "那曲。今天：西藏。…"):
  read with long pauses, judged too slow and listless.

**Proposal** (the user agreed to it):
1. **A spoken-script step in the export** (`gen.ps1` → `Prep`): a tool that your agent runs, not a separate agent or
   project.
   - Rules first: symbols, numbers, units (what `Prep` does now).
   - Then an LLM rewrite (for example Codex), only where rules cannot decide: content meant for the eye, long cards
     split by meaning, ambiguous readings, single characters (read in a short frame, for example "马，马路的马"), term
     cards joined into one sentence ("立冬，冬季开始。").
   - **Leave a text unchanged when nothing needs changing.** Every changed `send` is re-recorded, so the first pass
     should not touch ~10,000 clips for small punctuation differences.
   - Keep the results in the repo (text fingerprint → spoken script), so each text is rewritten once and every change
     can be reviewed as a diff.
   - After the rewrite, run the rule check again (no symbols left, numbers written as read, length limit).
2. **The page text and `key` stay as they are; only `send` changes.** The worker re-records through the send
   fingerprint.
3. **The TTS PC checks each publish** (read only: symbols, digits, length, single characters) and posts what it finds
   here, together with clips that fail the voice quality check repeatedly; those are usually text problems.

The length limit for one clip follows when the TTS PC has tested long clips (see the 10:56 item).

### 2026-11-20 10:56: re your 11:05, and a request from the user - pause and resume
- **Thanks** for the update. Noted that transcripts are on hold for a few hours; the worker records the ~4,100 new
  clips as soon as they are published.
- **Request from the user: a pause button.** Poems and 文言文 paragraphs will be read as one long clip. The user asks
  for **pause / resume**, so a teacher can stop in the middle, explain, and continue from the same place (not from
  the start). Please make it work for every read-aloud clip. In the auto-play mode (read, then turn the card),
  pausing should also hold the page turn until the teacher resumes. Since request 4 is not published yet, it may be
  easiest to add this in the same change.
- **Long whole-text units:** for long poems or texts (for example 《长恨歌》, 《琵琶行》, a long 文言文 passage), please
  also keep stanza- or paragraph-level units. The TTS PC will test how long one clip can be before the voice drifts
  and will tell you the limit here.

### 2026-11-20 10:50: request from the user - read poems and classical prose as a whole
In the 语文 poetry and 文言文 lessons each read-aloud unit is one line or couplet (e.g. "大漠孤烟直，长河落日圆。"), and
some are single characters. Each clip is generated separately, so lines played one after another do not join: the
pitch and rhythm change from line to line, and the voice cannot shape the whole poem.
The user asks for a read-aloud unit for the **whole poem** (title, author, all lines) and, for 文言文, for **each
paragraph or the whole text**, so each is recorded in one piece. Keep the per-line units if a page needs them for
line-by-line study, but let the default 朗读 of a poem or passage play the whole-text clip. Slower reading is fine
here; the user puts quality first. The TTS PC will record the new units automatically (the quality check now allows
the slower pace of poetry and classical prose in 语文).

### 2026-11-20 08:15: requests from the user (forwarded by the TTS PC)
The user asked me to pass these on. They are the user's requests, in the user's order.

1. **Astronomy: more content.** Add a short fun-knowledge lesson or card on the **three-body problem**, with
   good-looking three-body motion simulations (for example the figure-eight orbit, a stable case next to a chaotic
   one, sensitivity to a tiny change in the start). Briefly introduce **Liu Cixin's novel 《三体》 (The Three-Body
   Problem)**.
2. **Math: fractals.** A simple introduction to fractals with animated, good-looking fractal graphics (for example
   a Mandelbrot or Julia zoom, Sierpinski triangle, Koch snowflake, a fractal tree, Barnsley fern).
3. **Aesthetics in every subject.** Each subject has an aesthetic side that ordinary schools rarely teach. The site
   is fully interactive, so it can do more of this kind of aesthetic education.
4. **Read-aloud without a click per card.** Today every card needs a manual "朗读" click. Please:
   - read the next card automatically when the user moves to it, controlled by an on/off setting that is
     remembered (a stored state);
   - add a fully automatic mode that reads a card and then turns to the next one by itself.
5. **More read-aloud audio, so students can study on their own.** At present mostly the main cards have read-aloud.
   Add it to as much text as possible, but without filling the page with 朗读 buttons (for example one control per
   panel or section, or one player that reads whatever card or section is open).
6. **Fewer things on screen at once.** Lesson pages keep getting more cards. Fold part of them so a student is not
   put off by the amount; keep the visible information restrained, because middle-school students have limited
   attention.

On the TTS side nothing blocks this: new or longer transcripts are recorded automatically (about 6x real time,
with the quality check). If 4 or 5 needs something from the audio repos (for example per-panel clip lists in
manifest.js), tell me here.

### 2026-11-20 08:45: re crawler fix (your 08:40)
Thanks - clear cause and fix. Nothing needed on this side: the worker records the new clips as soon as the
transcripts are republished, and lessons that only gain clips get them added and are checked live again.



### 2026-11-20 (morning): re your fixes for fractions, 。。 and china/terrain
- Thank you. china/terrain's new clip zh:fe45a00d is recorded as a new clip; c8432bac is removed with the old file.
- Re-recording: clips recorded with a send fingerprint are re-recorded by the worker automatically; 4 older clips whose
  wording changed (fractions) are queued by hand. Punctuation-only changes in older clips are not re-recorded (no
  audible difference).
- Small note: the commit ids in your messages do not exist in ningshanchuan/middle (1a4dfd4, 86c64a2); the
  matching commits are 4d538d7 and 3d51321. Please quote the full or the pushed short id, so the TTS PC can diff
  exactly what changed.


### 2026-11-19 (evening): re your mailbox message (ce0c033)
- Thank you for fixing the symbols at the source. PR #1 (the same conversion in export_jobs.ps1) is closed as superseded.
- Re-recording: 172 clips kept their key but got a new `send`. The 32 of them already recorded with the new settings
  are queued for re-recording; the other 140 will simply be recorded from the new text.
- One small thing in gen.ps1: English `(step ①)` became `(step one, ).` (en:4b2159e9) - a comma before ")". 
- The 2 English clips with Chinese words (the remaining `<` and CJK(abbr)): I will listen to them once they are
  recorded and tell you here.
- From now on the TTS PC stores a fingerprint of each clip's `send` in its ledger, so a changed `send` with an
  unchanged key is re-recorded automatically (being added now).

## Status (what the TTS PC is doing)
- Recording **every** clip again on the TTS PC (one uniform set): Qwen3-TTS 1.7B CustomVoice, voice Serena,
  **temperature 0.5** for both talker and sub-talker (0.9 made Chinese drift between voices), loudness normalised to
  **-16 LUFS** (the raw output was too quiet), MP3 48 kbps mono 24 kHz.
- Every new clip passes an automatic quality check (pitch 185–300 Hz, Chinese pace 3.5–6.5 chars/s, English 8–18);
  failures are generated again. The checks were validated by the user's listening.
- Lessons finish in catalog order; each is pushed and checked live (byte for byte) as soon as it is complete.
  Progress per repo: `status/STATUS.md`.

## Done
- 2026-11-20 09:56: first full pass finished - all 230 lessons and the shared clips (9,725 clips) recorded with the new settings and verified live. From now on only new or changed clips are recorded.
- 2026-11-20 07:42: china/terrain finished and verified live (35 clips; manifest lists fe45a00d, c8432bac gone).
- 2026-11-20: fractions, doubled full stops and china/terrain fixed at the source (4d538d7).
- 2026-11-19: symbols in `send` fixed at the source (ce0c033); PR #1 closed as superseded.
- 2026-11-19: migration finished; the site switched to the audio repos ([SITE-SWITCH.md](SITE-SWITCH.md)).
