import asyncio
import json
import re
from playwright.async_api import async_playwright

HEADERS = {
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Helpers
def clean_price(raw: str) -> float | None:
    """
    Extract a float price from messy strings like:
      'R$\xa01.299,90', '1.130', '989\n.00', '1.299,90'
    """
    # Remove whitespace, newlines, non-breaking spaces
    raw = raw.replace("\xa0", "").replace(" ", "").replace("\n", "").strip()

    # Remove currency symbol
    raw = raw.replace("R$", "").strip()

    # Find the last price-like pattern in the string
    match = re.search(r"[\d.,]+", raw)
    if not match:
        return None

    value = match.group()

    # Brazilian format: 1.299,90 → 1299.90
    if "," in value and "." in value:
        value = value.replace(".", "").replace(",", ".")
    elif "," in value:
        # Decimal comma: 1299,90 → 1299.90
        value = value.replace(",", ".")
    elif "." in value:
        # If exactly 3 digits after dot → thousand separator (1.130 → 1130)
        parts = value.split(".")
        if len(parts) == 2 and len(parts[1]) == 3:
            value = value.replace(".", "")
        # Otherwise keep as-is (989.00 stays 989.00)

    try:
        result = float(value)
        # Sanity check: prices should be between R$1 and R$500.000
        if 1.0 <= result <= 500000.0:
            return result
        return None
    except ValueError:
        return None


# Mercado Livre
async def scrape_mercadolivre(page, query: str, max_results: int) -> list[dict]:
    results = []
    url = f"https://lista.mercadolivre.com.br/{query.replace(' ', '-')}"
    print(f"  [Mercado Livre] Fetching: {url}")

    # wait_until="networkidle" handles redirects properly
    await page.goto(url, wait_until="networkidle", timeout=40000)
    await page.wait_for_timeout(2000)

    items = await page.query_selector_all("li.ui-search-layout__item")
    print(f"  [Mercado Livre] Found {len(items)} raw items")

    for item in items[:max_results]:
        try:
            # Title + link are on the same <a> tag
            link_el = await item.query_selector("a.poly-component__title")
            price_int_el = await item.query_selector("span.andes-money-amount__fraction")
            price_dec_el = await item.query_selector("span.andes-money-amount__cents")

            if not link_el or not price_int_el:
                continue

            title = (await link_el.inner_text()).strip()
            link = await link_el.get_attribute("href") or ""

            price_int = (await price_int_el.inner_text()).strip()
            price_dec = (await price_dec_el.inner_text()).strip() if price_dec_el else "00"

            price = clean_price(f"{price_int},{price_dec}")
            if price is None:
                continue

            results.append({
                "marketplace": "Mercado Livre",
                "title": title,
                "price": price,
                "url": link,
            })
        except Exception as e:
            print(f"  [Mercado Livre] Error parsing item: {e}")
            continue

    return results


# Amazon BR
async def scrape_amazon(page, query: str, max_results: int) -> list[dict]:
    results = []
    url = f"https://www.amazon.com.br/s?k={query.replace(' ', '+')}"
    print(f"  [Amazon BR] Fetching: {url}")

    await page.goto(url, wait_until="networkidle", timeout=40000)
    await page.wait_for_timeout(2000)

    items = await page.query_selector_all("div[data-component-type='s-search-result']")
    print(f"  [Amazon BR] Found {len(items)} raw items")

    for item in items[:max_results]:
        try:
            title_el = await item.query_selector("h2 span")
            # a-offscreen contains the clean price string, e.g. "R$\xa01.299,90"
            price_el = await item.query_selector("span.a-price > span.a-offscreen")
            link_el = await item.query_selector("h2 a")

            if not title_el or not price_el:
                continue

            title = (await title_el.inner_text()).strip()
            raw_price = (await price_el.inner_text()).strip()
            price = clean_price(raw_price)
            if price is None:
                continue

            href = await link_el.get_attribute("href") if link_el else ""
            link = f"https://www.amazon.com.br{href}" if href.startswith("/") else href

            results.append({
                "marketplace": "Amazon BR",
                "title": title,
                "price": price,
                "url": link,
            })
        except Exception as e:
            print(f"  [Amazon BR] Error parsing item: {e}")
            continue

    return results


# Magalu
async def scrape_magalu(page, query: str, max_results: int) -> list[dict]:
    results = []
    url = f"https://www.magazineluiza.com.br/busca/{query.replace(' ', '%20')}/"
    print(f"  [Magalu] Fetching: {url}")

    await page.goto(url, wait_until="networkidle", timeout=40000)
    await page.wait_for_timeout(3000)

    # Primary selector
    items = await page.query_selector_all("a[data-testid='product-card-container']")

    # Fallback
    if not items:
        items = await page.query_selector_all("li[data-testid='product-item'] a")

    print(f"  [Magalu] Found {len(items)} raw items")

    for item in items[:max_results]:
        try:
            title_el = await item.query_selector("[data-testid='product-title']")
            price_el = await item.query_selector("[data-testid='price-value']")

            # Fallback selectors
            if not title_el:
                title_el = await item.query_selector("h2, h3, [class*='Title'], [class*='title']")
            if not price_el:
                price_el = await item.query_selector("[class*='price'], [class*='Price'], [class*='valor']")

            if not title_el or not price_el:
                continue

            title = (await title_el.inner_text()).strip()
            raw_price = (await price_el.inner_text()).strip()
            price = clean_price(raw_price)
            if price is None:
                continue

            link = await item.get_attribute("href") or ""
            if link.startswith("/"):
                link = f"https://www.magazineluiza.com.br{link}"

            results.append({
                "marketplace": "Magalu",
                "title": title,
                "price": price,
                "url": link,
            })
        except Exception as e:
            print(f"  [Magalu] Error parsing item: {e}")
            continue

    return results


# Diagnostic helper
async def diagnose(url: str, selector: str):
    """
    Opens a VISIBLE browser so you can see what's happening,
    then prints the text of the first 3 matched elements.

    Example usage at the bottom of this file:
        asyncio.run(diagnose("https://www.magazineluiza.com.br/busca/Samsung%20Galaxy%20A15/", "a[data-testid='product-card-container']"))
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(locale="pt-BR")
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle", timeout=40000)
        await page.wait_for_timeout(3000)
        items = await page.query_selector_all(selector)
        print(f"\nSelector '{selector}' matched {len(items)} elements")
        for i, el in enumerate(items[:3]):
            print(f"\n--- Element {i+1} ---")
            print(await el.inner_text())
        input("\nBrowser is open — press Enter to close...")
        await browser.close()


# ---------------------------------------------------------------------------
# Main scraper orchestrator
# ---------------------------------------------------------------------------

SCRAPERS = {
    "mercadolivre": scrape_mercadolivre,
    "amazon": scrape_amazon,
    "magalu": scrape_magalu,
}


async def run_scraper(
    query: str,
    marketplaces: list[str],
    max_results: int = 10,
) -> list[dict]:
    """
    Scrape the given marketplaces for `query`.
    Returns a flat list of product dicts, each with:
        marketplace, title, price (float, BRL), url
    """
    all_results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            extra_http_headers=HEADERS,
            locale="pt-BR",
        )

        for mp in marketplaces:
            mp_key = mp.lower()
            if mp_key not in SCRAPERS:
                print(f"  [!] Unknown marketplace: {mp_key}, skipping.")
                continue

            page = await context.new_page()
            try:
                results = await SCRAPERS[mp_key](page, query, max_results)
                print(f"  [{mp_key}] Collected {len(results)} valid listings")
                all_results.extend(results)
            except Exception as e:
                print(f"  [{mp_key}] Scraper failed: {e}")
            finally:
                await page.close()

        await browser.close()

    return all_results


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    query = "Samsung Galaxy A15"
    marketplaces = ["mercadolivre", "amazon", "magalu"]

    print(f"\nSearching for: '{query}'")
    print(f"Marketplaces : {', '.join(marketplaces)}\n")

    results = asyncio.run(run_scraper(query, marketplaces, max_results=5))

    print(f"\n{'='*60}")
    print(f"Total results collected: {len(results)}")
    print(f"{'='*60}\n")

    for r in results:
        print(f"[{r['marketplace']}] {r['title'][:60]:<60}  R$ {r['price']:.2f}")

    with open("scraper_output.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\nResults saved to scraper_output.json")