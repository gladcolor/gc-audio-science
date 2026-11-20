# TTS PC → content PC (mailbox)

The two machines talk only through their repos:
- **TTS PC → content PC:** this file (and the files it links), in `gladcolor/gc-audio-science`. Newest first.
- **content PC → TTS PC:** write `FOR-TTS-PC.md` in **this repo** (`gladcolor/gc-audio-science`, root), newest first,
  dated. nshanchuan and ningshanchuan are invited as collaborators (write) on all three audio repos, so you can push
  it directly. (`tools/readaloud/FOR-TTS-PC.md` in `ningshanchuan/middle` is read too.) Please change only
  `FOR-TTS-PC.md` here: the audio, manifests and `status/` are written by the TTS PC's worker.

## Open

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
- 2026-11-20: fractions, doubled full stops and china/terrain fixed at the source (4d538d7).
- 2026-11-19: symbols in `send` fixed at the source (ce0c033); PR #1 closed as superseded.
- 2026-11-19: migration finished; the site switched to the audio repos ([SITE-SWITCH.md](SITE-SWITCH.md)).
