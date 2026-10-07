import asyncio
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

OUT = Path("data/captures")

async def capture(url: str, timeout_ms: int = 20000, output_dir: Path = OUT) -> dict:
    """Capture an explicitly authorized HTTP(S) page and its evidence artifacts."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("url must be an absolute http(s) URL")
    output_dir.mkdir(parents=True, exist_ok=True)
    url_id = hashlib.sha1(url.encode()).hexdigest()[:16]
    shot_path = output_dir / f"{url_id}.png"
    dom_path = output_dir / f"{url_id}.html"
    net_path = output_dir / f"{url_id}.json"

    # Apply stealth to the entire Playwright context
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        ctx = await browser.new_context(
            viewport={"width": 1366, "height": 900},
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/123.0.0.0 Safari/537.36"),
            locale="en-IN",
        )
        page = await ctx.new_page()
        await stealth_async(page)

        requests_log: list[dict[str, str]] = []
        page.on("request", lambda request: requests_log.append({
            "url": request.url, "method": request.method,
            "resource": request.resource_type,
        }))

        result = {"url": url, "url_id": url_id, "ok": False, "requests": str(net_path)}
        try:
            resp = await page.goto(url, timeout=timeout_ms, wait_until="networkidle")
            await page.wait_for_timeout(500)
            await page.screenshot(path=str(shot_path), full_page=True)
            html = await page.content()
            dom_path.write_text(html, encoding="utf-8")
            net_path.write_text(json.dumps(requests_log, indent=2), encoding="utf-8")
            result.update({
                "ok": True,
                "status": resp.status if resp else None,
                "final_url": page.url,
                "title": await page.title(),
                "screenshot": str(shot_path),
                "dom": str(dom_path),
            })
        except Exception as error:
            result["error"] = str(error)
        finally:
            await browser.close()
        return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m backend.crawler.capture https://example.com")
    print(json.dumps(asyncio.run(capture(sys.argv[1])), indent=2))