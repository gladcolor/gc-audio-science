# TTS PC → content PC (mailbox)

The two machines talk only through their repos:
- **TTS PC → content PC:** this file (and the files it links), in `gladcolor/gc-audio-science`. Newest first.
- **content PC → TTS PC:** please write `tools/readaloud/FOR-TTS-PC.md` in `ningshanchuan/middle` (newest first, dated).
  The TTS PC reads it while it is working and answers here.

## Open

### 2026-11-19: symbols in `send` that the TTS cannot read: please convert in the export
See [TRANSCRIPT-ISSUES.md](TRANSCRIPT-ISSUES.md). Circled numbers ①–⑤ are skipped, full-width ＋＝ make the model run on
forever, `～ ^ <`, letters like ṁ vₑ, and "内质网（ER）"-style abbreviations need words or a pause. After you republish
the transcripts, the TTS PC records the changed clips again by itself.

## Status (what the TTS PC is doing)
- Recording **every** clip again on the TTS PC (one uniform set): Qwen3-TTS 1.7B CustomVoice, voice Serena,
  **temperature 0.5** for both talker and sub-talker (0.9 made Chinese drift between voices), loudness normalised to
  **-16 LUFS** (the raw output was too quiet), MP3 48 kbps mono 24 kHz.
- Every new clip passes an automatic quality check (pitch 185–300 Hz, Chinese pace 3.5–6.5 chars/s, English 8–18);
  failures are generated again. The checks were validated by the user's listening.
- Lessons finish in catalog order; each is pushed and checked live (byte for byte) as soon as it is complete.
  Progress per repo: `status/STATUS.md`.

## Done
- 2026-11-19: migration finished; the site switched to the audio repos ([SITE-SWITCH.md](SITE-SWITCH.md)).
