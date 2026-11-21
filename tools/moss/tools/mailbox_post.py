"""Add an entry to the top of the "## Open" section of FOR-CONTENT-PC.md in gladcolor/gc-audio-science, through the
GitHub contents API (never through the worker's working tree). Uses `gh` (signed in as gladcolor).
  python mailbox_post.py <entry.md> "<commit message>"      prints the new commit id"""
import base64, json, subprocess, sys, tempfile
from pathlib import Path

PATH = "repos/gladcolor/gc-audio-science/contents/FOR-CONTENT-PC.md"


def gh(*args, data=None):
    r = subprocess.run(["gh", "api", *args], capture_output=True, text=True, encoding="utf-8", input=data)
    if r.returncode:
        raise SystemExit(r.stderr.strip() or r.stdout.strip())
    return r.stdout


def main():
    entry = Path(sys.argv[1]).read_text(encoding="utf-8").rstrip("\n") + "\n\n"
    cur = json.loads(gh(PATH))
    text = base64.b64decode(cur["content"]).decode("utf-8")
    if text.count("## Open\n\n") != 1:
        raise SystemExit("FOR-CONTENT-PC.md has no single '## Open' heading")
    new = text.replace("## Open\n\n", "## Open\n\n" + entry, 1).encode("utf-8")
    payload = {"message": sys.argv[2], "content": base64.b64encode(new).decode(), "sha": cur["sha"]}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(payload, f)
    print(json.loads(gh("-X", "PUT", PATH, "--input", f.name))["commit"]["sha"])
    Path(f.name).unlink()


if __name__ == "__main__":
    main()
