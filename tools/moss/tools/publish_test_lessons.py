"""Publish already-recorded MOSS test clips (E:\\gc-audio\\_test\\lessons\\<lesson>\\zh\\<key>.mp3) for a few lessons,
through the worker's own code: each clip must belong to the CURRENT transcript (else it is skipped); it is copied into
the audio repo, written to the ledger with the MOSS voice tag, then the lesson is finished (manifest.js, timing.js,
status, commit, push) and checked live. Only the given lessons and only Chinese are touched.
  E:\\gc-audio\\venv-moss\\Scripts\\python.exe publish_test_lessons.py <lesson> [<lesson> ...]"""
import json, shutil, sys, types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tts_worker_next as W                              # noqa: E402

TEST = Path("E:/gc-audio/_test/lessons")


def main():
    lessons = sys.argv[1:]
    cfg = W.load_config(Path(__file__).resolve().parent / "tts_config_moss.json")
    W.LOGFILE = Path(cfg["root"]) / "worker.log"
    args = types.SimpleNamespace(fake=True, no_push=False, lesson="", loop=False, retry_failed=False, limit=0)
    w = W.Worker(cfg, args)
    entries = {e["id"]: e for e in w.index()}
    for lid in lessons:
        e = entries[lid]; repo = w.repos[e["repo"]]
        b = W.fetch(cfg["transcripts"] + lid + ".json")
        if b is None or W.fp12(b) != e["fingerprint"]:
            W.log(f"{lid}: transcript not available or changed - skipped"); continue
        tr = json.loads(b.decode("utf-8"))
        want = {(c["lang"], c["key"]): c for c in tr["clips"]}
        n = missing = 0
        for (lang, key), c in want.items():
            if lang != "zh":
                continue
            src = TEST / lid.replace("/", "__") / "zh" / f"{key}.mp3"
            if not src.exists():
                missing += 1; continue
            dst = repo.path / lid / "zh" / f"{key}.mp3"
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            w.add(repo, lid, "zh", key, cfg["kbps"], "tts", W.send_hash(c["send"]))
            n += 1
        W.log(f"{lid}: {n} MOSS test clips placed, {missing} zh clips without a test recording")
        w.finish(repo, lid, e, want, f"{lid}: read-aloud (MOSS-TTS test, zh)")
    w.check_pending(wait=True)                           # waits for GitHub Pages, then checks the live files


if __name__ == "__main__":
    main()
