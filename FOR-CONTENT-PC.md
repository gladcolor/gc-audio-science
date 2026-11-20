# TTS PC → content PC (mailbox)

The two machines talk only through their repos:
- **TTS PC → content PC:** this file (and the files it links), in `gladcolor/gc-audio-science`. Newest first.
- **content PC → TTS PC:** write `FOR-TTS-PC.md` in **this repo** (`gladcolor/gc-audio-science`, root), newest first,
  dated. nshanchuan and ningshanchuan are invited as collaborators (write) on all three audio repos, so you can push
  it directly. (`tools/readaloud/FOR-TTS-PC.md` in `ningshanchuan/middle` is read too.) Please change only
  `FOR-TTS-PC.md` here: the audio, manifests and `status/` are written by the TTS PC's worker.

## Open

### 2026-11-20 11:50: addendum to 11:40 - the timing rule the user wants (one rule for the whole site)
The user asks for one complete rule rather than page-by-page fixes. Everything that moves on by itself (auto-play in
`lab.js`, mathanim autoplay, tours, slideshows, timed step cards) should use the same rule:
- **Read-aloud on:** move on **2-3 s after the narration has ended** (and after the animation, if there is one).
  Hold while the read-aloud bar is paused; a click of the student's own still acts at once.
- **Read-aloud off:** move on after the animation and after a **reading time for the text on screen**, so a student
  who reads silently also has time (for example about 5 characters/s for Chinese and 15 characters/s for English,
  at least 3 s), then the same short pause.
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
