import asyncio
import os
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

# Path to your real Chrome profile — this uses your existing cookies/login
CHROME_PROFILE = os.path.expanduser(
    r"C:\Users\hsopg\AppData\Local\Google\Chrome\User Data"
)

async def diagnose():
    async with async_playwright() as p:
        # Use your real Chrome profile instead of a blank browser
        context = await p.chromium.launch_persistent_context(
            user_data_dir=CHROME_PROFILE,
            headless=False,
            channel="chrome",        # use your actual installed Chrome
            locale="pt-BR",
            args=["--profile-directory=Default"],
        )

        page = await context.new_page()
        await stealth_async(page)

        url = "https://lista.mercadolivre.com.br/Samsung-Galaxy-A15"
        print(f"Opening: {url}")

        # Wait for final navigation to settle
        await page.goto(url, wait_until="networkidle", timeout=40000)
        await page.wait_for_timeout(3000)

        # Keep waiting until URL stops changing
        prev_url = ""
        for _ in range(10):
            await page.wait_for_timeout(1000)
            current_url = page.url
            print(f"  Current URL: {current_url}")
            if current_url == prev_url:
                print("  URL settled.")
                break
            prev_url = current_url

        print(f"\nFinal URL: {page.url}")

        if "captcha" in page.url or "login" in page.url or "signup" in page.url:
            print("\n  Blocked — redirected to login/captcha page.")
        else:
            print("\n  Clean page! Testing selectors...")
            selectors = [
                "li.ui-search-layout__item",
                "a.poly-component__title",
                "div.poly-card",
                "ol.ui-search-layout > li",
            ]
            for sel in selectors:
                try:
                    items = await page.query_selector_all(sel)
                    print(f"  {len(items):>3}  matches  →  {sel}")
                except Exception as e:
                    print(f"  ERR  →  {sel}  ({e})")

        input("\nBrowser is open — inspect the page, then press Enter to close.")
        await context.close()

asyncio.run(diagnose())