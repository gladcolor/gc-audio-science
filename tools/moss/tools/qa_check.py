"""Read current recording ledgers and write quality reports under _test/qa."""

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from html import escape
from io import StringIO
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import re
from statistics import median
import subprocess
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / "_test" / "qa"
REPOS = ("gc-audio-science", "gc-audio-humanities", "gc-audio-lang-math")
TRANSCRIPTS = "https://shanchuan.org/middle/readaloud"
AUDIO = "https://gladcolor.github.io"
SAMPLE_RATE = 16_000
PACE = {"en": (8, 18), "zh": (3, 7)}
FIELDS = (
    "repo", "lesson", "lang", "key", "duration", "chars", "chars_per_s",
    "f0_median", "lufs", "flags",
)
LOUDNESS = re.compile(
    r"\bSummary:\s*Integrated loudness:\s*I:\s*"
    r"([+-]?(?:\d+(?:\.\d+)?|inf))\s+LUFS\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Clip:
    repo: str
    lesson: str
    lang: str
    key: str
    size: int
    mtime_ns: int

    @property
    def id(self):
        return f"{self.repo}/{self.lesson}/{self.lang}/{self.key}"

    @property
    def path(self):
        return ROOT / f"{self.id}.mp3"

    def matches(self, entry):
        return (
            entry.get("size") == self.size
            and entry.get("mtime_ns") == self.mtime_ns
            and all(field in entry for field in ("duration", "f0_median", "lufs"))
        )


def write_text(path, content):
    """Publish a complete file after writing it beside its destination."""
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)
    temporary.replace(path)


def write_json(path, data):
    write_text(path, json.dumps(data, ensure_ascii=False, allow_nan=False))


def read_ledgers(repos, voice_tag):
    clips = {}
    missing = 0
    for repo in repos:
        ledger = ROOT / repo / "status" / "ledger.tsv"
        with ledger.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                if row["voice"] != voice_tag:
                    continue
                lesson, lang, key = (row[field] for field in ("lesson", "lang", "key"))
                path = ROOT / repo / lesson / lang / f"{key}.mp3"
                if not path.is_file():
                    missing += 1
                    continue
                try:
                    info = path.stat()
                except FileNotFoundError:
                    missing += 1
                    continue
                clip = Clip(repo, lesson, lang, key, info.st_size, info.st_mtime_ns)
                clips[clip.id] = clip
    return list(clips.values()), missing


def analyze(job):
    import librosa
    import numpy as np

    clip, ffmpeg = job
    try:
        result = subprocess.run(
            [
                ffmpeg, "-hide_banner", "-nostdin", "-nostats",
                "-threads", "1", "-i", str(clip.path),
                "-map", "0:a:0", "-af", "ebur128=framelog=verbose", "-f", "null", "-",
                "-map", "0:a:0", "-ac", "1", "-ar", str(SAMPLE_RATE),
                "-c:a", "pcm_f32le", "-f", "f32le", "pipe:1",
            ],
            capture_output=True,
            check=True,
            timeout=120,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        summaries = LOUDNESS.findall(result.stderr.decode("utf-8", errors="replace"))
        samples = np.frombuffer(result.stdout, dtype="<f4")
        if not summaries or not samples.size:
            raise ValueError("FFmpeg returned no loudness summary or audio samples")

        f0, voiced, _ = librosa.pyin(
            samples, fmin=120, fmax=600, sr=SAMPLE_RATE, frame_length=1024,
        )
        voiced_f0 = f0[voiced & np.isfinite(f0)]
        lufs = float(summaries[-1])
        info = clip.path.stat()
        if (info.st_size, info.st_mtime_ns) != (clip.size, clip.mtime_ns):
            raise ValueError("MP3 changed during analysis")
        return {
            "size": clip.size,
            "mtime_ns": clip.mtime_ns,
            "duration": samples.size / SAMPLE_RATE,
            "f0_median": float(np.median(voiced_f0)) if voiced_f0.size else None,
            "lufs": lufs if math.isfinite(lufs) else str(lufs),
        }, None
    except subprocess.CalledProcessError as error:
        stderr = error.stderr.decode("utf-8", errors="replace").strip().splitlines()
        return {}, stderr[-1] if stderr else str(error)
    except Exception as error:
        return {}, str(error)


def get_transcripts(lessons):
    cache = QA / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    transcripts = {}
    problems = {}
    network_error = None

    for lesson in sorted(lessons):
        local = cache / f"{quote(lesson, safe='')}.json"
        try:
            if local.is_file():
                payload = json.loads(local.read_text(encoding="utf-8-sig"))
            else:
                if network_error is not None:
                    problems[lesson] = network_error
                    continue
                remote = "shared" if lesson == "_shared" else quote(lesson, safe="/")
                with urlopen(f"{TRANSCRIPTS}/{remote}.json", timeout=8) as response:
                    payload = json.loads(response.read())
            if not isinstance(payload, dict) or not isinstance(payload.get("clips"), list):
                raise ValueError("Expected a JSON object with a clips list")
            transcripts[lesson] = {
                (item.get("lang"), item.get("key")): item["send"]
                for item in payload["clips"]
                if isinstance(item, dict)
                and isinstance(item.get("lang"), str)
                and isinstance(item.get("key"), str)
                and isinstance(item.get("send"), str)
            }
            if not local.is_file():
                write_json(local, payload)
        except HTTPError as error:
            problems[lesson] = f"HTTP {error.code}"
        except (URLError, TimeoutError) as error:
            network_error = str(error)
            problems[lesson] = network_error
        except (OSError, ValueError) as error:
            problems[lesson] = str(error)

    return transcripts, problems


def make_row(clip, metrics, transcripts):
    send = transcripts.get(clip.lesson, {}).get((clip.lang, clip.key))
    duration = metrics.get("duration")
    chars = len(send) if send is not None else None
    lufs = metrics.get("lufs")
    return {
        "repo": clip.repo, "lesson": clip.lesson, "lang": clip.lang, "key": clip.key,
        "duration": duration, "chars": chars,
        "chars_per_s": chars / duration if chars is not None and duration else None,
        "f0_median": metrics.get("f0_median"),
        "lufs": float(lufs) if lufs is not None else None,
        "flags": [], "send": send, "f0_distance": -1,
    }


def median_metric(rows, field):
    values = [row[field] for row in rows if row[field] is not None]
    return median(values) if values else None


def flag_clips(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["lang"]].append(row)

    summaries = {}
    for lang, clips in sorted(groups.items()):
        pitches = [row["f0_median"] for row in clips if row["f0_median"] is not None]
        center = median(pitches) if pitches else None
        mad = median(abs(pitch - center) for pitch in pitches) if pitches else None
        for row in clips:
            reasons = row["flags"]
            pitch = row["f0_median"]
            if pitch is not None:
                distance = abs(pitch - center)
                row["f0_distance"] = distance
                if pitch < 170:
                    reasons.append("F0 below 170 Hz")
                elif pitch > 300:
                    reasons.append("F0 above 300 Hz")
                if distance > 2.5 * 1.4826 * mad:
                    reasons.append("F0 more than 2.5 robust z-scores from language median")

            pace = row["chars_per_s"]
            if lang in PACE and pace is not None:
                low, high = PACE[lang]
                if pace < low:
                    reasons.append(f"Pace below {low:g} chars/s")
                elif pace > high:
                    reasons.append(f"Pace above {high:g} chars/s")

            lufs = row["lufs"]
            if lufs is not None:
                if lufs < -18:
                    reasons.append("Loudness below -18 LUFS")
                elif lufs > -14:
                    reasons.append("Loudness above -14 LUFS")

        summaries[lang] = (
            len(clips), sum(bool(row["flags"]) for row in clips),
            sum(row["chars_per_s"] is None for row in clips),
            median_metric(clips, "duration"), center, mad,
            median_metric(clips, "chars_per_s"), median_metric(clips, "lufs"),
        )
    return summaries


def display(value):
    if value is None:
        return "Unknown"
    return f"{value:.2f}" if isinstance(value, float) else str(value)


def write_reports(rows, summaries):
    buffer = StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS)
    writer.writeheader()
    for row in rows:
        record = {field: row[field] for field in FIELDS}
        record["flags"] = "; ".join(row["flags"])
        writer.writerow(record)
    write_text(QA / "report.csv", buffer.getvalue())

    flagged = sorted(
        (row for row in rows if row["flags"]),
        key=lambda row: (-len(row["flags"]), -row["f0_distance"]),
    )
    page = ["""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Read-aloud recording QA</title>
<style>
:root { color-scheme: light dark; }
body { max-width: 68rem; margin: 2rem auto; padding: 0 1rem;
       font: 1rem/1.5 system-ui, sans-serif; }
table { border-collapse: collapse; }
th, td { border: 1px solid GrayText; padding: .35rem .6rem; text-align: left; }
.table { overflow-x: auto; }
article { border-top: 1px solid GrayText; margin: 1.25rem 0; }
h3 { overflow-wrap: anywhere; }
.transcript { white-space: pre-wrap; overflow-wrap: anywhere; }
audio { max-width: 100%; }
</style>
<h1>Read-aloud recording QA</h1>
<h2>Language summary</h2>
<div class="table"><table><thead><tr>
<th>Language</th><th>Clips</th><th>Flagged</th><th>Unknown pace</th>
<th>Median duration (s)</th><th>Median F0 (Hz)</th><th>F0 MAD (Hz)</th>
<th>Median pace (chars/s)</th><th>Median loudness (LUFS)</th>
</tr></thead><tbody>
"""]
    for lang, values in summaries.items():
        cells = "".join(f"<td>{escape(display(value))}</td>" for value in values)
        page.append(f'<tr><th scope="row">{escape(lang)}</th>{cells}</tr>')
    page.append("</tbody></table></div>")
    page.append(f"<h2>Flagged clips ({len(flagged)})</h2>")
    for row in flagged:
        parts = [row[field] for field in ("repo", "lesson", "lang", "key")]
        title = escape(" / ".join(parts))
        # the page lives in <root>/_test/qa/: play the local file (lessons not pushed yet are not online)
        url = escape(f"../../{quote('/'.join(parts), safe='/')}.mp3", quote=True)
        send = escape(row["send"] if row["send"] is not None else "Transcript unavailable")
        reasons = "".join(f"<li>{escape(reason)}</li>" for reason in row["flags"])
        page.append(f"""
<article>
<h3>{title}</h3>
<p class="transcript" lang="{escape(row['lang'], quote=True)}">{send}</p>
<p>Duration {display(row['duration'])} s · Characters {display(row['chars'])}
 · Pace {display(row['chars_per_s'])} chars/s · F0 {display(row['f0_median'])} Hz
 · Loudness {display(row['lufs'])} LUFS</p>
<ul>{reasons}</ul>
<audio controls preload="none" src="{url}"></audio>
</article>""")
    write_text(QA / "flagged.html", "\n".join(page) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, help="Maximum number of new or changed clips")
    parser.add_argument("--repo", choices=REPOS, help="Scan one recording repository")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 0:
        parser.error("--limit must be nonnegative")

    config_path = ROOT / "tools" / "tts_config.json"
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    clips, missing = read_ledgers((args.repo,) if args.repo else REPOS, config["voice_tag"])
    QA.mkdir(parents=True, exist_ok=True)
    cache_path = QA / "metrics.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}

    reusable = {clip.id: cache[clip.id] for clip in clips if clip.matches(cache.get(clip.id, {}))}
    uncached = [clip for clip in clips if clip.id not in reusable]
    pending = uncached[:args.limit]
    errors = []
    if pending:
        ffmpeg = Path(config["ffmpeg"])
        if not ffmpeg.is_file():
            parser.error(f"FFmpeg executable not found: {ffmpeg}")
        print(f"Analyzing {len(pending)} clips with six CPU workers.", flush=True)
        pool = mp.get_context("spawn").Pool(processes=6)
        try:
            jobs = ((clip, str(ffmpeg)) for clip in pending)
            results = pool.imap(analyze, jobs)
            for clip, (metrics, error) in zip(pending, results):
                if error is not None:
                    errors.append((clip.id, error))
                else:
                    reusable[clip.id] = cache[clip.id] = metrics
        finally:
            pool.close()
            pool.join()
        write_json(cache_path, cache)
    elif not cache_path.exists():
        write_json(cache_path, cache)

    included = reusable.keys() | {clip.id for clip in pending}
    reported = [clip for clip in clips if clip.id in included]
    transcripts, transcript_errors = get_transcripts({clip.lesson for clip in reported})
    rows = [make_row(clip, reusable.get(clip.id, {}), transcripts) for clip in reported]
    summaries = flag_clips(rows)
    write_reports(rows, summaries)

    flagged = sum(bool(row["flags"]) for row in rows)
    print(f"{len(rows)} clips reported, {flagged} flagged.")
    print(f"{len(clips) - len(uncached)} cached, {len(pending)} attempted, "
          f"{len(uncached) - len(pending)} deferred, {missing} missing MP3s.")
    for lang, (total, flagged_count, unknown, *_) in summaries.items():
        print(f"  {lang}: {total} clips, {flagged_count} flagged, {unknown} with unknown pace")

    reasons = Counter(reason for row in rows for reason in row["flags"])
    top = ", ".join(f"{reason} ({count})" for reason, count in reasons.most_common(5))
    print(f"Top reasons: {top or 'none'}")
    unknown_transcripts = sum(row["send"] is None for row in rows)
    if unknown_transcripts:
        print(f"Transcript text unavailable for {unknown_transcripts} clips. "
              "Their pace is unknown.")
    if transcript_errors:
        print(f"Transcript retrieval or cache errors for {len(transcript_errors)} lessons.")
        for lesson, error in list(transcript_errors.items())[:3]:
            print(f"  {lesson}: {error}")
    if errors:
        print(f"Audio analysis failed for {len(errors)} clips.")
        for clip_id, error in errors[:3]:
            print(f"  {clip_id}: {error}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
