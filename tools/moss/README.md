# TTS PC code: read-aloud audio for shanchuan.org/middle

This is all TTS code from the TTS PC as of 2026-11-21, copied from its `E:\gc-audio`. Personal paths are replaced by `<HOME>`; the code contains no tokens.

- Engine in production: **MOSS-TTS-Local-Transformer-v1.5 (4B)**, Serena voice cloned from three references.
- Old engine, kept for comparison: Qwen3-TTS-12Hz-1.7B-CustomVoice.
- Everything ran on Windows, Python 3.12, RTX GPU with 24 GB. None of it was tested on Linux or Colab.

```
tools/   all Python / PowerShell / cmd code and both configs (tts_config.json = Qwen, tts_config_moss.json = MOSS)
wsl/     setup scripts used in WSL Ubuntu 24.04 (MOSS env, Docker + NVIDIA toolkit for SGLang-Omni; not used in production)
refs/    Serena reference recordings + refs.json (their texts and sources)
requirements-moss.txt / requirements-qwen.txt   package versions that worked
```

## 1. Models (Hugging Face, revisions used)

| role | repo | revision |
| --- | --- | --- |
| 4B TTS (production) | `OpenMOSS-Team/MOSS-TTS-Local-Transformer-v1.5` | `be7766a6735b98bd793f7c79fb720b4d0f5d13b8` |
| its codec | `OpenMOSS-Team/MOSS-Audio-Tokenizer-v2` | `f6e20e543b33d2c252a7ef71bdf8aa71e5ff9169` |
| 8B TTS (tested compressed only) | `OpenMOSS-Team/MOSS-TTS-v1.5` | `cdd3b911b1585e3f2dbc7775ef10f9926f58850a` |
| its codec | `OpenMOSS-Team/MOSS-Audio-Tokenizer` | `3cd226ba2947efa357ef453bcad111b6eafba782` |

- The model code comes with the model repos (`trust_remote_code=True`). Documentation: github.com/OpenMOSS/MOSS-TTS.
- Packages: see `requirements-moss.txt` (torch 2.9.1 cu128, transformers 5.0.0). **No flash-attn**: there is no prebuilt wheel for Windows, and in WSL a partial install broke `import transformers`. We use `attn_implementation="sdpa"` and `torch.backends.cuda.enable_cudnn_sdp(False)`.
- Loading (4B), as in `tools/moss_engine.py` class `Moss`:

```python
proc = AutoProcessor.from_pretrained(MODEL, trust_remote_code=True, codec_path=CODEC)
proc.audio_tokenizer = proc.audio_tokenizer.to("cuda")          # do NOT cast the codec to bf16 yourself (dtype error)
model = AutoModel.from_pretrained(MODEL, trust_remote_code=True, attn_implementation="sdpa",
                                  dtype=torch.bfloat16).to("cuda").eval()
```

- **Output.** The 4B codec returns 48 kHz stereo. We average to mono and resample to 24 kHz with ffmpeg. The 8B codec returns 24 kHz mono.

## 2. Voice

- `refs/serena_zh_poem.mp3`: 春望, recited. Used for verse and wenyan.
- `refs/serena_zh_explain.mp3`: an astronomy explanation. Used for Chinese explanations and prose.
- `refs/serena_en_explain.mp3`: an English explanation.
- Texts and sources are in `refs/refs.json`.
- All three were recorded on this PC with the Qwen3 Serena voice.

How a reference is passed:
1. ffmpeg decodes the mp3 to 24 kHz mono float32.
2. `codes = proc.encode_audios_from_wav([wav], 24000)[0]`.
3. Each request is `proc.build_user_message(text=..., language="Chinese"|"English", reference=[codes])`.

Notes:
- The reference transcript is **not** passed; MOSS clones from the audio.
- 4B: `wav` is a 1-D tensor. **8B: `wav` must be `[channels, samples]`**, i.e. `wav[None, :]`.

## 3. Reading rules (MOSS)

The code is `tools/moss_engine.py`. These are the user's settings of 2026-11-20 and 2026-11-21.

**Settings from the Qwen period that do not apply to MOSS:**
- temperature 0.5;
- 15 tries for science;
- target durations;
- QA pace 3.5–6.5.

**Kind of each clip**, from the transcript field `style`:
- `verse` / `wenyan` → poem;
- `prose` → prose;
- no field → explanation;
- every English clip → en.

**Pause markers** (`with_pauses`):
- Chinese: `[pause 0.8s]` after 。！？ when more text follows.
- Whole-poem units "题目。作者。正文": `[pause 1.0s]` after the title and after the author.
- English: `[pause 0.8s]` after . ! ? followed by a space and a capital letter, quote or bracket (not after a digit).

**Pace targets**, in characters per second over the whole clip, pauses included. Counting uses `speech_len`: Latin letters count 0.4, digits 3.

| kind | target |
| --- | --- |
| poem, ≤100 chars | 2.5 |
| poem, >100 chars | 3.0 |
| prose | 3.5 (proposed, awaiting approval) |
| explanation, science subjects | 3.8 |
| explanation, everyday-life lessons (`"pace": "brisk"` in the index) | 4.1 |
| explanation, other | 4.0 |
| English | none |

- Mood per work: light +0.2, somber −0.2 (`moods.proposed.json`, awaiting approval on #3).

**Sampling:** model defaults, `audio_temperature=1.7, audio_top_p=0.8, audio_top_k=25, audio_repetition_penalty=1.0`. **No target duration** (`tokens`): forced durations sounded monotonous, and about 11 % of the clips then got a stray sound at the end.

**Tries:** up to 5 free tries per clip. If no try passes the check, the try with the lowest score is kept.

**Check** (`check`):
- pitch (librosa pyin median F0): 175–300 Hz;
- pace within target ±0.5, only when speech_len ≥ 15;
- no stray sound at the end: a sound of ≤ 0.6 s after a pause of ≥ 0.5 s; skipped when the last sentence has ≤ 3 characters;
- not longer than 2 × expected + 3 s;
- score = |pace − target| / target + 10 × number of failed checks.

**Batching:**
- clips sorted by length, ≤ 8 per batch, ≤ 180 s of expected audio per batch;
- `max_new_tokens` = (2 × longest expected + 10 s) × 12.5 + 25;
- about 13–15 GB of VRAM with the 4B;
- an OOM splits the batch.

**Encode** (`to_mp3`, `loudness_filter` in `tts_worker.py`):
1. ffmpeg `loudnorm` measures the clip.
2. A linear gain brings it to **−16 LUFS** (true peak ≤ −1.5 dB).
3. libmp3lame, **48 kbps, mono, 24 kHz**.

**Speed on this PC:** about 5.6 × real time for one pass of the 4B, about 1.2 × real time with retries.

## 4. Text normalization

**Layer 1 is not implemented yet.** The worker reads `send` exactly as given: hook `spoken(clip)` in `tts_worker.py` returns `clip["send"]`. There is nothing to port.

## 5. Output, ledger, order: `tools/tts_worker.py`

**Repos.** Every lesson in `readaloud/index.json` names its repo: gc-audio-science, gc-audio-humanities or gc-audio-lang-math. The audio files are `<subject>/<topic>/<lang>/<key>.mp3`.

**Per lesson** the worker writes `manifest.js` and `timing.js` (clip durations).

**Per repo**, in `status/`:
- `ledger.tsv`, columns `lang key lesson voice kbps date source send`; `send` is the first 10 hex characters of a hash of the send text;
- `lessons.json`;
- `STATUS.md`.

**Pass:**
1. Read `index.json`.
2. For each lesson, in catalog order:
   - delete orphan clips;
   - list the clips still missing;
   - skip held lessons (`hold_lessons`), clips with `style` (until `record_styled`) and demand clips (until `record_demand`).
3. Pool the clips of all lessons into the length-sorted batches.
4. When a lesson's last clip is in, finish it: manifest + timing + ledger, commit, push, wait for GitHub Pages, compare the live files byte for byte.

**Voice tag.** Every ledger row carries the config's `voice_tag`. This PC uses `serena moss15`. **Rows with any other tag are recorded again by this PC** (`Repo.__init__`).

**Run on this PC:**

```
venv-moss\Scripts\python.exe tools\tts_worker.py run --loop --config tools\tts_config_moss.json
```

- This command runs under `supervise_moss.ps1`, which restarts the worker if it hangs.
- Paths in the configs are Windows paths: `root` is `E:/gc-audio`, and the `ffmpeg` path is under `<HOME>`.
- `init` checks the repo clones and the transcripts.
- `test-voice` makes one test clip per language.
- `status` prints the progress.

## 6. If Colab records (read before starting)

1. **Model choice is site-wide.**
   - The 4B and the 8B do not sound the same.
   - If Colab records with the 8B and this PC later continues with the 4B, the site has two voices.
   - Recommendation: on Colab, first record the same 3 test lessons with the 8B (biology/cell-theory, china/ming-qing, yuwen/yw-tang-poems). Put them next to the 4B versions now live, on a listening page. The user then picks one model for the whole site.
2. **Voice tag.**
   - 4B on Colab: same rules, `voice_tag: "serena moss15"`. This PC can then continue from the ledger.
   - 8B: needs its own tag, e.g. `serena moss8b`. This PC then records those lessons again, unless the user chooses the 8B for the whole site. On this PC the 8B runs only compressed, at 0.25–0.5 × real time, so the whole site would then be recorded on Colab.
3. **One writer at a time.**
   - Colab and this PC must not record the same repo at the same time.
   - This PC stays stopped until the user restarts it.
   - Before this PC resumes, Colab stops and all its pushes are in. This PC then pulls and continues from the ledger.
   - This PC's gc-audio-science working tree has 30 uncommitted MOSS clips from biology/* (in progress when the GPU hung). Colab should start from the pushed state; this PC discards or re-records those.

## 7. 8B notes

- Tested only compressed with bitsandbytes (`tools/bench_moss8b.py`):
  - 8-bit filled 20 GB and spilled into shared memory, at 0.25 × real time;
  - 4-bit nf4 ran at 0.5 × real time;
  - the user did not judge the quality.
- Uncompressed bf16: about 16–17 GB for weights and codec, plus the batch. That fits on an A100 or L4 with 24 GB or more.
- It uses a different codec (v1, 24 kHz mono), and the reference shape is `[1, samples]`.
- All rules above were tuned on the 4B. Check the pauses (0.8 s / 1.0 s), the pace and the stray-end rate again by listening.

## 8. Qwen3 (old engine)

`tools/tts_config.json` + `tts_worker.py` with `engine` unset:
- Qwen3-TTS-12Hz-1.7B-CustomVoice, speaker Serena, temperature 0.5;
- QA: F0 185–300 Hz, pace zh 3.5–6.5 / en 8–18, 5 tries (15 for science).

It was replaced because:
- sentence ends got no clear pause;
- clips over about 150 characters often stopped part-way.
