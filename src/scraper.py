import asyncio
import json
import re
from playwright.sync_api import sync_playwright
from seleniumbase import sb_cdp

sb = sb_cdp.Chrome()
endpoint_url = sb.get_endpoint_url()

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
    

# ---------------------------------------------------------------------------
# Main scraper orchestrator
# ---------------------------------------------------------------------------

def get_results(page, compact: list, search: str, max_results: int):
    """ Take the link, the search bar, goes to the link, click on the bar,
        Fill the bar search, keyboard confirm, get all the elements.
    """
    link = compact[0]
    search_bar = compact[1]
    page.goto(link)
    page.click(search_bar)
    page.fill(search_bar, search)
    page.keyboard.press("Enter") 
    page.wait_for_timeout(4000)
    
    # Locate all individual product card elements
    found_products = page.locator('li.ui-search-layout__item').all()
    print(f"Products list found. Total elements located: {len(found_products)}")
    
    products_data_list = []
    product_count = 0

    # Iterate through the located cards up to the max_results limit
    for product_card in found_products[:max_results]:
        product_count += 1
        print(f"\n--- Processing Product Number: {product_count} ---")
        
        try:
            # 1. Extract Title
            title = product_card.locator('a.poly-component__title').first.inner_text()
            
            # 2. Extract Product Link
            product_link = product_card.locator('a.poly-component__title').first.get_attribute('href')
            
            # 3. Extract Rating (with a fallback if it doesn't exist)
            try:
                rating = product_card.locator('span.polylabel-label').first.inner_text()
            except:
                rating = "No rating available"
            
            # 4. Extract Price
            # We target the element holding the aria-label attribute for a clean string
            price_element = product_card.locator('.poly-price__current span[role="img"]').first
            if price_element.count() > 0:
                current_price = price_element.get_attribute('aria-label')
            else:
                current_price = "Price unavailable"
            
            # 5. Extract Item Condition
            try:
                condition = product_card.locator('span.poly-component__item-condition').first.inner_text()
            except:
                condition = "New"
            
            # 6. Extract Shipping Information
            try:
                shipping = product_card.locator('.poly-component__shipping-v2').first.inner_text().strip()
            except:
                shipping = "Not specified"

            # Structure the extracted data into a dictionary
            product_details = {
                "title": title,
                "link": product_link,
                "rating": rating,
                "price": current_price,
                "condition": condition,
                "shipping": shipping
            }
            
            # Append to the final list and display the successful result
            products_data_list.append(product_details)
            print(f"Successfully scraped: {product_details['title']}")
            print(product_details)
            
        except Exception as error:
            # This will now print the exact error message if the scraping fails for a card
            print(f"❌ Failed to scrape product number {product_count}. Error: {error}")
            continue 

    # Close the page after the loop finishes processing all items
    page.close() 
    
    #return products_data_list


LINKS = {
    "mercadolivre": ["https://lista.mercadolivre.com.br/", "#cb1-edit"],
    "amazon": ["https://www.amazon.com.br/"],
    "magalu": ["https://www.magazineluiza.com.br/"],
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
            link = LINKS[mp]
            if mp_key not in LINKS:
                print(f"  [!] Unknown marketplace: {mp_key}, skipping.")
                continue

            try:
                results = get_results(page, link, query, max_results)
                print(f"  [{mp_key}] Collected {len(results)} valid listings")
                all_results.extend(results)
            except Exception as e:
                print(f"  [{mp_key}] Scraper failed: {e}")
            finally:
                page.close()

        browser.close()

    return all_results


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    query = "Samsung Galaxy A15"
    marketplaces = ["mercadolivre", "amazon", "magalu"]
    print(f"\nSearching for: '{query}'")
    #print(f"Marketplaces : {', '.join(marketplaces)}\n")

    run_scraper(query, marketplaces, max_results=5)

    """
    print(f"\n{'='*60}")
    print(f"Total results collected: {len(results)}")
    print(f"{'='*60}\n")

    for r in results:
        print(f"[{r['marketplace']}] {r['title'][:60]:<60}  R$ {r['price']:.2f}")

    with open("scraper_output.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\nResults saved to scraper_output.json")"""