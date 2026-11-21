"""Test: does an auto-advancing step player cut its narration short?  Opens a live page in headless Chrome (the
installed Chrome, not Playwright's headless shell), optionally replaces shared/mathanim.js by a local file, turns on
the narration (🔊) of the first step player, starts autoplay and logs every recording (play / pause / ended with
position) and every step change.  Read only.
  python test_narration.py <page url> [local mathanim.js] [--voice-off]"""
import json, sys, time
from pathlib import Path

from playwright.sync_api import sync_playwright

INIT = r"""
window.__log = []; const t0 = performance.now(); const log = (k, o) => window.__log.push(Object.assign({k, t: (performance.now() - t0) / 1000}, o));
const P = HTMLMediaElement.prototype, play = P.play;
P.play = function(){ if (!this.__w){ this.__w = 1;
    for (const e of ['playing', 'pause', 'ended']) this.addEventListener(e, () => { if (!this.muted || e !== 'playing') log(e, {src: (this.src || '').split('/').slice(-3).join('/'), pos: +this.currentTime.toFixed(2), dur: +(this.duration || 0).toFixed(2), muted: this.muted}); }); }
  return play.apply(this, arguments); };
new MutationObserver(() => { const s = document.querySelector('.ma-step'); const v = s && s.textContent; if (v && v !== window.__step){ window.__step = v; log('step', {step: v}); } })
  .observe(document, {subtree: true, childList: true, characterData: true});
"""


def main():
    url = sys.argv[1]
    local = next((a for a in sys.argv[2:] if a.endswith(".js")), None)
    voice = "--voice-off" not in sys.argv
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True, args=["--autoplay-policy=no-user-gesture-required"])
        try:
            pg = b.new_page()
            if local:
                body = Path(local).read_text(encoding="utf-8")
                pg.route("**/shared/mathanim.js*", lambda r: r.fulfill(body=body, content_type="application/javascript"))
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
            pg.add_init_script(INIT)
            pg.goto(url, wait_until="load", timeout=60000)
            pg.wait_for_timeout(3000)
            bar = pg.locator(".ma-player").first
            bar.scroll_into_view_if_needed()
            if voice:
                bar.locator("button[data-a=voice]").click()
                pg.wait_for_timeout(300)
            bar.locator("button[data-a=play]").click()
            t = time.time()
            while time.time() - t < 240:                   # until autoplay ends (button says ▶ again)
                pg.wait_for_timeout(2000)
                if "⏸" not in bar.locator("button[data-a=play]").inner_text():
                    break
            pg.wait_for_timeout(1500)
            log = pg.evaluate("window.__log")
        finally:
            b.close()
    print(f"{url}  narration {'on' if voice else 'off'}  mathanim: {local or 'live'}  page errors: {errs or 'none'}")
    steps = [e for e in log if e["k"] == "step"]
    cut = 0
    for i, s in enumerate(steps):
        nxt = steps[i + 1]["t"] if i + 1 < len(steps) else 1e9
        ev = [e for e in log if e["k"] != "step" and s["t"] <= e["t"] < nxt and not e.get("muted")]
        start = next((e for e in ev if e["k"] == "playing"), None)
        end = next((e for e in ev if e["k"] in ("ended", "pause") and e["t"] > (start["t"] if start else 0)), None)
        if end is None:                                # stopped by the next step's start?
            end = next((e for e in log if e["k"] in ("ended", "pause") and nxt <= e["t"] < nxt + 0.5), None)
        full = bool(end and (end["k"] == "ended" or end["pos"] >= end["dur"] - 0.3))
        cut += bool(start) and not full
        gap = f"{nxt - end['t']:5.1f}s" if (end and nxt < 1e9) else "   - "
        print(f"  step {s['step']:>5s} at {s['t']:6.1f}s  narration "
              + (f"{start['dur']:5.1f}s  {'ended' if full else 'CUT at %.1fs' % end['pos'] if end else 'no end'}"
                 if start else "none          ")
              + f"  -> next step {gap} after the narration")
    print(f"  {len(steps)} steps, {cut} narration(s) cut")


if __name__ == "__main__":
    main()
