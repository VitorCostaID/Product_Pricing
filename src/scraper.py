from playwright.sync_api import sync_playwright
from seleniumbase import sb_cdp
from bs4 import BeautifulSoup

sb = sb_cdp.Chrome()
endpoint_url = sb.get_endpoint_url()

# ---------------------------------------------------------------------------
# Main scraper orchestrator
# ---------------------------------------------------------------------------

def get_results(page, references: list, search: str, max_results: int):
    """ Take the link, the search bar, goes to the link, clicks on the bar,
        Fills the bar search, keyboard confirms, and quickly extracts data.
    """
    link = references[0]
    search_bar = references[1]
    page.goto(link)
    page.click(search_bar)
    page.fill(search_bar, search)
    page.wait_for_timeout(200)
    page.keyboard.press("Enter")

    # Wait until the search results structure is physically on the page
    page.wait_for_selector(references[2])
    
    # ⚡ LIGHTNING HANDOFF: Grab raw HTML and close the browser immediately
    html_content = page.content()
    
    # Parse the HTML with the built-in parser (No installation needed)
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
        
        product_details = {
            "title": title_el.get_text() if title_el else "Unknown",
            "link": title_el.get('href') if title_el else "#",
            "rating": rating_el.get_text() if rating_el else "No rating available",
            "price": price_el.get('aria-label') if price_el else "Price unavailable",
            "condition": condition_el.get_text() if condition_el else "New",
            "shipping": shipping_el.get_text().strip() if shipping_el else "Not specified"
        }
        products_data_list.append(product_details)
        print(product_details)
        
    return products_data_list


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
    
    "mercadolivre": [
        "https://lista.mercadolivre.com.br/", 
        "#cb1-edit", 
        "li.ui-search-layout__item",
        "a.poly-component__title", 
        "span.polylabel-label", 
        ".poly-price__current span[role='img']", 
        "span.poly-component__item-condition", 
        ".poly-component__shipping-v2"
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
    ]
}


def run_scraper(
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

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(endpoint_url)
        page = browser.contexts[0].pages[0]

        # Test if the marketplace is at dictionary
        for mp in marketplaces:
            mp_key = mp.lower()
            link = REFS[mp]
            if mp_key not in REFS:
                print(f"  [!] Unknown marketplace: {mp_key}, skipping.")
                continue

            try:
                results = get_results(page, link, query, max_results)
                print(f"  [{mp_key}] Collected {len(results)} valid listings")
                all_results.extend(results)
            except Exception as e:
                print(f"  [{mp_key}] Scraper failed: {e}")

        browser.close()

    return all_results


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

listed = ["mercadolivre", "amazon", "magalu"]
check = [True, True, False]
marketplaces = []

for index, value in enumerate(check):
    if value == True:
        marketplaces.append(listed[index])

if __name__ == "__main__":
    query = "Samsung Galaxy A15"
    print(f"\nSearching for: '{query}'")
    print(f"Marketplaces : {', '.join(marketplaces)}\n")

    all_results = run_scraper(query, marketplaces, max_results=5)