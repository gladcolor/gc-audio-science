"""Check (issue #6): turning a card by hand while it is being read stops the narration; with auto-read on, the new card
is read. Headless Chrome (installed Chrome), real clicks. For each page: find the first visible 🔊 inside a card that
also has a Next / 下一 button, click 🔊, wait, click Next mid-clip, then report what is playing.
  python test_manual_turn.py <url> [<url> ...]"""
import sys

from playwright.sync_api import sync_playwright

INIT = r"""
window.__ev = []; const t0 = performance.now(); const log = (k, o) => window.__ev.push(Object.assign({k, t: +((performance.now() - t0) / 1000).toFixed(1)}, o));
const P = HTMLMediaElement.prototype, play = P.play;
P.play = function(){ if (!this.__w){ this.__w = 1;
  for (const e of ['playing', 'pause', 'ended']) this.addEventListener(e, () => { if (!this.muted || e !== 'playing') log(e, {src: (this.src || '').split('/').pop(), pos: +this.currentTime.toFixed(1)}); }); }
  return play.apply(this, arguments); };
const hook = () => { if (!window.Lab || !Lab.speak || Lab.__h) return; Lab.__h = 1; const sp = Lab.speak;
  Lab.speak = function(text){ log('speak', {text: String(text).slice(0, 30)}); return sp.apply(this, arguments); }; };
const iv = setInterval(hook, 20); setTimeout(() => clearInterval(iv), 20000);
"""
FIND = r"""() => {
  const vis = el => el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden';
  const spk = [...document.querySelectorAll('button')].filter(b => vis(b) && /🔊|朗读/.test(b.textContent) && !b.closest('.lab-nav,#lab-nav,.lab-player,.ma-player'));
  for (const s of spk) {
    let box = s.parentElement;
    for (let k = 0; k < 6 && box; k++, box = box.parentElement) {
      const nx = [...box.querySelectorAll('button')].find(b => vis(b) && b !== s && /下一|Next|▶/.test(b.textContent) && !/播放|play|朗读/i.test(b.textContent));
      if (nx) { s.setAttribute('data-t-spk', '1'); nx.setAttribute('data-t-next', '1'); return [s.textContent.trim().slice(0, 20), nx.textContent.trim().slice(0, 20)]; }
    }
  }
  return null; }"""


def run(pw, url, auto_read):
    b = pw.chromium.launch(channel="chrome", headless=True, args=["--autoplay-policy=no-user-gesture-required"])
    try:
        pg = b.new_page()
        pg.add_init_script(INIT + f"localStorage.setItem('labAutoRead', '{'1' if auto_read else '0'}'); localStorage.setItem('labAutoNext', '0');")
        pg.goto(url + ("&" if "?" in url else "?") + "nocache=1", wait_until="load", timeout=60000)
        pg.wait_for_timeout(3000)
        found = pg.evaluate(FIND)
        if not found:
            return "no card with both 🔊 and Next found"
        pg.locator("[data-t-spk]").first.scroll_into_view_if_needed()
        pg.locator("[data-t-spk]").first.click()
        pg.wait_for_timeout(4000)
        before = pg.evaluate("window.__ev.length")
        pg.locator("[data-t-next]").first.click()
        pg.wait_for_timeout(2500)
        ev = pg.evaluate("window.__ev")
        after = ev[before:]
        stopped = any(e["k"] == "pause" for e in after)
        new_speak = [e for e in after if e["k"] == "speak"]
        playing_new = [e for e in after if e["k"] == "playing"]
        return (f"buttons {found}; after Next: old clip stopped={stopped}, new speak={[e['text'] for e in new_speak]}, "
                f"new clip playing={bool(playing_new)}")
    finally:
        b.close()


def main():
    with sync_playwright() as pw:
        for url in sys.argv[1:]:
            for ar in (False, True):
                print(f"{url.split('/middle/')[-1]}  auto-read {'on ' if ar else 'off'}: {run(pw, url, ar)}", flush=True)


if __name__ == "__main__":
    main()
