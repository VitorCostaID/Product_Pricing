import asyncio
from playwright.async_api import async_playwright
from seleniumbase import sb_cdp
from bs4 import BeautifulSoup

sb = sb_cdp.Chrome()
endpoint_url = sb.get_endpoint_url()


REFS = { 
    # Index Positions mapped to variables inside get_results():
    # [0]: Base URL
    # [1]: Search Bar Selector
    # [2]: Container Product Card Selector
    # [3]: Title Anchor Selector
    # [4]: Rating Element Selector
    # [5]: Price Image/Label Selector
    # [6]: Condition Tag Selector
    # [7]: Shipping Container Selector
    # [8]: Product Page: Description Selector
    # [9]: Product Page: Review Text Selector
    
    "mercadolivre": [
        "https://lista.mercadolivre.com.br/", 
        "#cb1-edit", 
        "li.ui-search-layout__item",
        "a.poly-component__title", 
        "span.polylabel-label", 
        ".poly-price__current span[role='img']", 
        "span.poly-component__item-condition", 
        ".poly-component__shipping-v2",
        "p.ui-pdp-description__content",                 # [8] Description
        "p.ui-review-capability-comments__comment__text" # [9] Reviews

    ],
    
    "amazon": [
        "https://www.amazon.com.br/", 
        "#twotabsearchtextbox",                      # Amazon search bar ID
        'div[data-component-type="s-search-result"]',                       # Amazon individual card wrapper
        'a.a-text-normal',                         # Title anchor nested inside h2
        'span.a-a-size-small',                        # Text holding rating star counts
        'span.a-price span.a-offscreen',              # Clean hidden text price string
        'span.a-badge-text',                          # Fallback tag wrapper
        "span[aria-label*='frete']"                   # Target element mentioning shipping
        "#productDescription",                       # [8] Description
        "span[data-hook='review-body']"              # [9] Reviews
    ],
    
    "magalu": [
        "https://www.magazineluiza.com.br/",
        "#header-search-input",
        "li[data-testid='product-card']",            # Magalu card structural attribute
        "h3[data-testid='product-title']",
        "span.sc-eBMEME", 
        "p[data-testid='price-value']",
        "span.condition-placeholder",
        "div[data-testid='shipping-info']"
        "div[data-testid='product-description']",    # [8] Description (Example)
        "p[data-testid='review-description']"        # [9] Reviews (Example)
    ]
}

async def fetch_deep_data(context, product_details: dict, references: list, semaphore: asyncio.Semaphore):
    """
    Helper function that visits the product page to grab descriptions and reviews.
    The semaphore ensures only 3 of these run at the exact same time.
    """
    # If the link is invalid, skip deep scraping
    if product_details["link"] == "#":
        product_details["description"] = "No link available"
        product_details["reviews"] = []
        return product_details

    async with semaphore:
        page = await context.new_page()
        try:
            print(f"  ⚡ Deep scraping: {product_details['title'][:30]}...")
            await page.goto(product_details["link"], wait_until="domcontentloaded")
            await page.wait_for_timeout(1000) # Give React/Next.js time to mount text
            
            html_content = await page.content()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract Description [8]
            desc_el = soup.select_one(references[8])
            product_details["description"] = desc_el.get_text(separator="\n").strip() if desc_el else "Description unavailable"
            
            # Extract Top 5 Reviews [9]
            reviews = []
            review_elements = soup.select(references[9])[:5]
            for rev in review_elements:
                reviews.append(rev.get_text(separator=" ").strip())
                
            product_details["reviews"] = reviews

        except Exception as e:
            print(f"  ❌ Error deep scraping {product_details['title'][:15]}: {e}")
            product_details["description"] = "Failed to extract"
            product_details["reviews"] = []
        finally:
            await page.close()
            
        return product_details

async def get_results(page, references: list, search: str, max_results: int):
    """ Take the link, the search bar, goes to the link, clicks on the bar,
        Fills the bar search, keyboard confirms, and quickly extracts data.
    """
    link = references[0]
    search_bar = references[1]
    await page.goto(link)
    await page.click(search_bar)
    await page.fill(search_bar, search)
    await page.wait_for_timeout(500)
    await page.keyboard.press("Enter")

    # Wait until the search results structure is physically on the page
    await page.wait_for_selector(references[2])
    
    # Grab raw HTML and close the browser immediately
    html_content = await page.content()
    await page.close()
    
    # Parse the HTML with the built-in parser
    soup = BeautifulSoup(html_content, 'html.parser')
    product_cards = soup.select(references[2])[:max_results]
    
    print(f"Products list found. Total elements to parse: {len(product_cards)}")
    products_data_list = []
    
    for card in product_cards:
        title_el = card.select_one(references[3])
        rating_el = card.select_one(references[4])
        price_el = card.select_one(references[5])
        condition_el = card.select_one(references[6])
        shipping_el = card.select_one(references[7])

        product_link = title_el.get('href') if title_el else "#"
        product_link = f"{link}{product_link}"
        
        product_details = {
            "title": title_el.get_text() if title_el else "Unknown",
            "link": title_el.get('href') if title_el else "#",
            "rating": rating_el.get_text() if rating_el else "No rating available",
            "price": price_el.get('aria-label') if price_el else "Price unavailable",
            "condition": condition_el.get_text() if condition_el else "New",
            "shipping": shipping_el.get_text().strip() if shipping_el else "Not specified",
            "description": "",
            "reviews": []
        }
        products_data_list.append(product_details)

    # 3. Fire off the Deep Scrapers concurrently (Max 3 at a time)
    semaphore = asyncio.Semaphore(3)

    # This creates a list of background tasks
    tasks = [
        fetch_deep_data(page, product, references, semaphore)
        for product in products_data_list
    ]
    
    # `asyncio.gather` runs them all at once and waits for them to finish
    fully_enriched_products = await asyncio.gather(*tasks)
        
    return fully_enriched_products

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
        browser = await p.chromium.connect_over_cdp(endpoint_url)
        page = browser.contexts[0].pages[0]

        # Test if the marketplace is at dictionary
        for mp in marketplaces:
            mp_key = mp.lower()
            link = REFS[mp]
            if mp_key not in REFS:
                print(f"  [!] Unknown marketplace: {mp_key}, skipping.")
                continue

            link = REFS[mp_key]
            
            # Open a clean tab profile container for each distinct marketplace
            page = await browser.contexts[0].new_page()

            try:
                results = await get_results(page, link, query, max_results)
                print(f"  [{mp_key}] Collected {len(results)} valid listings")
                all_results.extend(results)
            except Exception as e:
                print(f"  [{mp_key}] Scraper failed: {e}")
            finally:
                # Close the context window tab cleanly before moving to next site
                await page.close()

        await browser.close()

    return all_results


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

listed = ["mercadolivre", "amazon", "magalu"]
check = [True, False, False]
marketplaces = []

for index, value in enumerate(check):
    if value == True:
        marketplaces.append(listed[index])

if __name__ == "__main__":
    query = "Samsung Galaxy A15"
    print(f"\nSearching for: '{query}'")
    print(f"Marketplaces : {', '.join(marketplaces)}\n")

    final_data = asyncio.run(run_scraper(query, marketplaces, max_results=5))

    # Print the final enriched payload
    for item in final_data:
        print(f"\nTitle: {item['title']}")
        print(f"Price: {item['price']}")
        print(f"Description Snippet: {item['description'][:100]}...")
        print(f"Total Reviews Pulled: {len(item['reviews'])}")