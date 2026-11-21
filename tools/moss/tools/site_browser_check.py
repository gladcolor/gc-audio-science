"""Open every lesson page of shanchuan.org/middle in headless Chromium (read only, no clicks) and record:
uncaught script errors, console errors, failed requests and HTTP >= 400 responses.
Writes E:\\gc-audio\\_test\\site_audit\\browser.md and browser.json.
  python site_browser_check.py            (conda python: it has playwright)"""
import asyncio, json, sys, time, urllib.request
from collections import defaultdict
from pathlib import Path

from playwright.async_api import async_playwright

INDEX = "https://shanchuan.org/middle/readaloud/index.json"
OUT = Path("E:/gc-audio/_test/site_audit")
PARALLEL = 4
SETTLE_MS = 6000


async def check(browser, lesson, url, sem, results):
    async with sem:
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900}, locale="zh-CN")
        page = await ctx.new_page()
        rec = {"lesson": lesson, "url": url, "pageerror": [], "console": [], "failed": [], "http": []}
        page.on("pageerror", lambda e: rec["pageerror"].append(str(e)[:300]))
        page.on("console", lambda m: rec["console"].append(m.text[:300]) if m.type == "error" else None)
        page.on("requestfailed", lambda r: rec["failed"].append(f"{r.failure} {r.url[:200]}")
                if "ERR_ABORTED" not in str(r.failure) else None)
        page.on("response", lambda r: rec["http"].append(f"{r.status} {r.url[:200]}") if r.status >= 400 else None)
        try:
            await page.goto(url, wait_until="load", timeout=60000)
            await page.wait_for_timeout(SETTLE_MS)
        except Exception as e:                           # noqa: BLE001
            rec["pageerror"].append(f"LOAD: {str(e)[:200]}")
        await ctx.close()
        results.append(rec)
        n = sum(len(rec[k]) for k in ("pageerror", "console", "failed", "http"))
        print(f"{len(results):3d} {lesson}: {n} problem(s)", flush=True)


async def main():
    idx = json.loads(urllib.request.urlopen(INDEX, timeout=60).read().decode("utf-8"))
    lessons = [(x["id"], x["url"]) for x in idx["lessons"]]
    if len(sys.argv) > 1:
        lessons = [l for l in lessons if any(a in l[0] for a in sys.argv[1:])]
    results, sem = [], asyncio.Semaphore(PARALLEL)
    t = time.time()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        await asyncio.gather(*(check(browser, l, u, sem, results) for l, u in lessons))
        await browser.close()
    OUT.mkdir(parents=True, exist_ok=True)
    results.sort(key=lambda r: r["lesson"])
    (OUT / "browser.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    by_msg = defaultdict(set)                            # the same problem on many pages -> one line
    for r in results:
        for kind in ("pageerror", "console", "failed", "http"):
            for m in set(r[kind]):
                by_msg[(kind, m)].add(r["lesson"])
    lines = ["# Browser check of every lesson page", "",
             f"{time.strftime('%Y-%m-%d %H:%M')}, {len(results)} pages, headless Chromium, no clicks, "
             f"{SETTLE_MS // 1000} s after load. {time.time() - t:.0f} s.", ""]
    names = {"pageerror": "Uncaught script errors", "console": "Console errors", "failed": "Failed requests",
             "http": "HTTP errors"}
    for kind, title in names.items():
        items = sorted(((m, ls) for (k, m), ls in by_msg.items() if k == kind), key=lambda x: (-len(x[1]), x[0]))
        lines += [f"## {title} ({len(items)})", ""]
        lines += [f"- {m}  \n  pages ({len(ls)}): " + ", ".join(sorted(ls)[:6]) + (" ..." if len(ls) > 6 else "")
                  for m, ls in items] or ["- none"]
        lines.append("")
    (OUT / "browser.md").write_text("\n".join(lines), encoding="utf-8")
    clean = sum(1 for r in results if not any(r[k] for k in names))
    print(f"done: {clean}/{len(results)} pages without problems; report {OUT / 'browser.md'}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
