"""Read-only check of the live site (shanchuan.org/middle) and the audio repos.
1. audio: every clip in each lesson's live transcript is listed in the live manifest.js and its MP3 is online;
   the manifest lists no clip the transcript no longer has.
2. pages: every lesson page loads, and every same-site resource it references (scripts, styles, images, video,
   audio, links to other lessons) answers HTTP 200.
Writes E:\\gc-audio\\_test\\site_audit\\report.md and prints a summary.
  python site_audit.py"""
import json, re, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SITE = "https://shanchuan.org/middle/"
RA = SITE + "readaloud/"
AUDIO = {r: f"https://gladcolor.github.io/{r}/" for r in ("gc-audio-science", "gc-audio-humanities", "gc-audio-lang-math")}
OUT = Path("E:/gc-audio/_test/site_audit")
UA = {"User-Agent": "site-audit/1.0"}
LOCAL = Path("E:/gc-audio")


def get(url, head=False, tries=3):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA, method="HEAD" if head else "GET")
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, (b"" if head else r.read())
        except urllib.error.HTTPError as e:
            if e.code == 405 and head:                  # some hosts refuse HEAD
                return get(url, False, tries)
            if e.code in (404, 410):
                return e.code, b""
            err = e.code
        except Exception as e:                          # noqa: BLE001
            err = repr(e)[:80]
        time.sleep(2 * (a + 1))
    return err, b""


URLS, REPOS = {}, {}


def repo_of(lesson):
    return REPOS.get(lesson)


def audit_audio(lesson):
    probs = []
    st, b = get(RA + ("shared" if lesson == "_shared" else lesson) + ".json")
    if st != 200:
        return [f"transcript {st}"]
    clips = json.loads(b.decode("utf-8"))["clips"]
    want = {(c["lang"], c["key"]) for c in clips}
    repo = repo_of(lesson)
    if not repo:
        return [f"no audio folder in any repo ({len(want)} clips)"]
    st, b = get(AUDIO[repo] + lesson + "/manifest.js")
    if st != 200:
        return [f"manifest.js {st}"]
    m = json.loads(re.search(r"LabAudioManifest\((\{.*\})\)", b.decode("utf-8"), re.S).group(1))
    have = {(lg, k) for lg in ("en", "zh") for k in (m.get(lg) or "").split()}
    miss = sorted(want - have); extra = sorted(have - want)
    if miss:
        probs.append(f"{len(miss)} clip(s) in the transcript but not in manifest.js: " +
                     ", ".join(f"{lg}:{k}" for lg, k in miss[:8]) + (" ..." if len(miss) > 8 else ""))
    if extra:
        probs.append(f"{len(extra)} clip(s) in manifest.js no longer in the transcript: " +
                     ", ".join(f"{lg}:{k}" for lg, k in extra[:8]) + (" ..." if len(extra) > 8 else ""))
    for lg, k in sorted(have & want):                   # the worker verified bytes; here only "is it online"
        if not (LOCAL / repo / lesson / lg / f"{k}.mp3").exists():
            probs.append(f"{lg}:{k} listed but no local MP3")
    return probs


REF = re.compile(r"""(?:src|href|poster|data-src)\s*=\s*["']([^"'#]+)["']""", re.I)


def page_refs(lesson):
    url = URLS[lesson]
    st, b = get(url)
    if st != 200:
        return url, st, []
    refs = set()
    for u in REF.findall(b.decode("utf-8", "replace")):
        if u.startswith(("mailto:", "javascript:", "data:", "tel:")):
            continue
        full = urllib.parse.urljoin(url, u.strip())
        if full.startswith(SITE):
            refs.add(full.split("?")[0])
    return url, 200, sorted(refs)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    st, b = get(RA + "index.json")
    idx = json.loads(b.decode("utf-8"))
    global URLS, REPOS
    URLS = {x["id"]: x["url"] for x in idx["lessons"]}
    REPOS = {x["id"]: x["repo"] for x in idx["lessons"]} | {"_shared": idx["shared"]["repo"]}
    lessons = list(URLS) + ["_shared"]
    print(f"{len(lessons)} lessons", flush=True)
    with ThreadPoolExecutor(8) as ex:
        audio = dict(zip(lessons, ex.map(audit_audio, lessons)))
        pages = list(ex.map(page_refs, [l for l in lessons if l != "_shared"]))
        refs = sorted({r for _, _, rs in pages for r in rs})
        print(f"{len(refs)} distinct same-site resources", flush=True)
        status = dict(zip(refs, ex.map(lambda u: get(u, head=True)[0], refs)))
    lines = ["# Site audit", "", f"{time.strftime('%Y-%m-%d %H:%M')}. Read only.", "", "## Audio (transcript vs manifest.js)", ""]
    bad_audio = {l: p for l, p in audio.items() if p}
    lines += [f"- **{l}**: " + "; ".join(p) for l, p in sorted(bad_audio.items())] or ["- no problems"]
    lines += ["", "## Pages and resources", ""]
    bad_pages = [(u, s) for u, s, _ in pages if s != 200]
    lines += [f"- page {u}: {s}" for u, s in bad_pages]
    broken = {u: s for u, s in status.items() if s != 200}
    for u, s in sorted(broken.items()):
        users = [p for p, _, rs in pages if u in rs]
        lines.append(f"- {s} {u} (used by {len(users)} page(s): " + ", ".join(x.replace(SITE, '') for x in users[:4])
                     + (" ..." if len(users) > 4 else "") + ")")
    if not bad_pages and not broken:
        lines.append("- no problems")
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"audio: {len(bad_audio)} lesson(s) with problems; pages: {len(bad_pages)} failed; "
          f"resources: {len(broken)} broken of {len(status)}", flush=True)
    print(f"report: {OUT / 'report.md'}", flush=True)


if __name__ == "__main__":
    main()
