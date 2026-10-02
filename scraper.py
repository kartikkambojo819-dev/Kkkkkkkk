import cloudscraper
import os
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'android',
        'mobile': True
    }
)

BASE_URL = "https://filmyzilla.digital/"
SAVE_DIR = "Filmyzilla_Cloned"

visited_urls = set()

def save_file(url, content):
    parsed = urlparse(url)
    path = parsed.path.lstrip('/')
    if not path or path.endswith('/'):
        path += "index.html"
        
    filepath = os.path.join(SAVE_DIR, path)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    mode = 'wb' if isinstance(content, bytes) else 'w'
    with open(filepath, mode, encoding='utf-8' if isinstance(content, str) else None) as f:
        f.write(content)
    print(f"[+ Saved] {filepath}")

def scrape_site(start_url, max_pages=300):
    queue = [start_url]
    
    while queue and len(visited_urls) < max_pages:
        current_url = queue.pop(0)
        
        if current_url in visited_urls:
            continue
            
        visited_urls.add(current_url)
        print(f"[*] [{len(visited_urls)}/{max_pages}] Scraping: {current_url}")
        
        try:
            response = scraper.get(current_url)
            if response.status_code == 200:
                save_file(current_url, response.text)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 1. Download Static Assets (Images, CSS, JS)
                for tag, attr in [('img', 'src'), ('link', 'href'), ('script', 'src')]:
                    for element in soup.find_all(tag):
                        asset_url = element.get(attr)
                        if asset_url and not asset_url.startswith('data:'):
                            full_asset_url = urljoin(current_url, asset_url)
                            if BASE_URL in full_asset_url and full_asset_url not in visited_urls:
                                try:
                                    res = scraper.get(full_asset_url)
                                    if res.status_code == 200:
                                        save_file(full_asset_url, res.content)
                                        visited_urls.add(full_asset_url)
                                except Exception:
                                    pass
                
                # 2. Extract Sub-links (<a> tags) for next pages
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    full_link = urljoin(current_url, href)
                    
                    # Only stay on same domain & skip external links
                    if BASE_URL in full_link and full_link not in visited_urls:
                        if not any(full_link.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.css', '.js']):
                            queue.append(full_link)
                            
            time.sleep(1) # IP Block se bachne ke liye delay
            
        except Exception as e:
            print(f"[!] Error fetching {current_url}: {e}")

if __name__ == "__main__":
    # max_pages ko zaroorat ke hisab se badha sakte hain (e.g. 500 ya 1000)
    scrape_site(BASE_URL, max_pages=300)
