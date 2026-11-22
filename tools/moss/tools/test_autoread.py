"""Which texts are read aloud, and in what order, when a step player runs on a page?  Opens the live page in headless
Chrome (installed Chrome), sets the read-aloud switches (auto-read / auto-play) as given, turns on the first step
player's narration, starts it, and logs every Lab.speak() text with its time, plus the step changes. Read only.
  python test_autoread.py <url> [--auto-read] [--auto-play] [--seconds 120]"""
import sys, time

from playwright.sync_api import sync_playwright

INIT = r"""
window.__log = []; const t0 = performance.now(); const log = (k, o) => window.__log.push(Object.assign({k, t: +((performance.now() - t0) / 1000).toFixed(1)}, o));
const hook = () => { if (!window.Lab || !Lab.speak || Lab.__h) return; Lab.__h = 1; const sp = Lab.speak;
  Lab.speak = function(text, o){ log('speak', {text: String(text).slice(0, 60)}); return sp.apply(this, arguments); }; };
const iv = setInterval(hook, 20); setTimeout(() => clearInterval(iv), 15000);
new MutationObserver(() => { const s = document.querySelector('.ma-step'); const v = s && s.textContent; if (v && v !== window.__step){ window.__step = v; log('step', {step: v}); } })
  .observe(document, {subtree: true, childList: true, characterData: true});
document.addEventListener('click', e => { if (!e.isTrusted){ const b = e.target.closest('button,[role=button]'); log('auto-click', {what: b ? (b.textContent || b.title || '').trim().slice(0, 30) + ' @' + (b.closest('section') || {}).id : '?'}); } }, true);
"""


def main():
    url = sys.argv[1]
    secs = int(sys.argv[sys.argv.index("--seconds") + 1]) if "--seconds" in sys.argv else 120
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", headless=True, args=["--autoplay-policy=no-user-gesture-required"])
        try:
            pg = b.new_page()
            if "--lab" in sys.argv:                      # test a local lab.js instead of the live one
                body = open(sys.argv[sys.argv.index("--lab") + 1], encoding="utf-8").read()
                pg.route("**/shared/lab.js*", lambda r: r.fulfill(body=body, content_type="application/javascript"))
            pg.add_init_script(INIT + ("localStorage.setItem('labAutoRead', '%s'); localStorage.setItem('labAutoNext', '%s');"
                                       % ("1" if "--auto-read" in sys.argv else "0", "1" if "--auto-play" in sys.argv else "0")))
            pg.goto(url, wait_until="load", timeout=60000)
            pg.wait_for_timeout(3000)
            bar = pg.locator(".ma-player").first
            bar.scroll_into_view_if_needed()
            bar.locator("button[data-a=voice]").click(); pg.wait_for_timeout(300)
            bar.locator("button[data-a=play]").click()
            pg.wait_for_timeout(secs * 1000)
            log = pg.evaluate("window.__log")
        finally:
            b.close()
    print(f"{url}  auto-read {'on' if '--auto-read' in sys.argv else 'off'}, auto-play {'on' if '--auto-play' in sys.argv else 'off'}")
    for e in log:
        print(f"  {e['t']:6.1f}s {e['k']:10s} {e.get('text') or e.get('step') or e.get('what') or ''}")


if __name__ == "__main__":
    main()
