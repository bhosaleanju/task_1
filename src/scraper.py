"""
Enterprise-Grade Books Scraper Module
Extracts book information from http://books.toscrape.com/ with retries, connection pooling,
and concurrent detail enrichment.
"""

import os
import time
from typing import List, Dict, Optional
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import pandas as pd

from src.config import CONFIG
from src.logger import get_logger
from src.models import RawBook
from src.exceptions import ScraperError

logger = get_logger("ScraperEngine")


class BooksScraper:
    """
    Automated, resilient web scraper for http://books.toscrape.com/.
    Supports multi-page catalog traversal, detail enrichment, and concurrent fetching.
    """

    def __init__(
        self,
        output_dir: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None
    ):
        self.output_dir = output_dir or CONFIG.paths.data_dir
        self.timeout = timeout or CONFIG.scraper.timeout_seconds
        self.max_retries = max_retries or CONFIG.scraper.max_retries
        os.makedirs(self.output_dir, exist_ok=True)

        self.session = self._create_resilient_session()

    def _create_resilient_session(self) -> requests.Session:
        """Configures a requests.Session with connection pooling and exponential backoff retries."""
        session = requests.Session()
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=CONFIG.scraper.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=25,
            pool_maxsize=25
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            "User-Agent": CONFIG.scraper.user_agent,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        })
        return session

    def scrape_catalog_page(self, page_num: int) -> List[RawBook]:
        """
        Scrapes a single catalogue page (contains up to 20 books).
        """
        url = f"{CONFIG.scraper.catalogue_url}page-{page_num}.html"
        logger.info(f"Fetching catalog page {page_num:02d}: {url}")

        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code != 200:
                logger.warning(f"Catalog page {page_num} responded with status {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            pods = soup.find_all("article", class_="product_pod")
            books_on_page: List[RawBook] = []

            for pod in pods:
                # 1. Title
                title_elem = pod.h3.find("a")
                title = title_elem.get("title", title_elem.text.strip()) if title_elem else "Unknown"

                # 2. Detail URL
                rel_link = title_elem["href"] if title_elem and "href" in title_elem.attrs else ""
                book_url = urljoin(url, rel_link)

                # 3. Price
                price_elem = pod.find("p", class_="price_color")
                price_raw = price_elem.text.strip() if price_elem else "N/A"

                # 4. Rating string
                rating_elem = pod.find("p", class_="star-rating")
                rating_str = "Unknown"
                if rating_elem and "class" in rating_elem.attrs:
                    classes = [c for c in rating_elem["class"] if c != "star-rating"]
                    if classes:
                        rating_str = classes[0]

                # 5. Availability string
                avail_elem = pod.find("p", class_="instock availability")
                availability_raw = avail_elem.text.strip() if avail_elem else "Unknown"

                # 6. Image URL
                img_elem = pod.find("img")
                img_url = urljoin(url, img_elem["src"]) if img_elem and "src" in img_elem.attrs else ""

                book = RawBook(
                    title=title,
                    price_raw=price_raw,
                    rating_str=rating_str,
                    availability_raw=availability_raw,
                    book_url=book_url,
                    image_url=img_url,
                    page_number=page_num
                )
                books_on_page.append(book)

            return books_on_page

        except requests.RequestException as e:
            logger.error(f"Network error on catalog page {page_num}: {e}")
            return []
        except Exception as e:
            logger.error(f"Parsing error on catalog page {page_num}: {e}")
            return []

    def scrape_book_details(self, book: RawBook) -> RawBook:
        """
        Fetches the individual book detail page to enrich with Category, UPC, Stock count, Tax, Description.
        """
        if not book.book_url:
            return book

        try:
            resp = self.session.get(book.book_url, timeout=self.timeout)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")

                # Category from breadcrumb: Home > Books > [Category] > [Title]
                breadcrumb = soup.find("ul", class_="breadcrumb")
                if breadcrumb:
                    items = [li.text.strip() for li in breadcrumb.find_all("li")]
                    if len(items) >= 3:
                        book.category = items[2]

                # Product Information Table
                table = soup.find("table", class_="table-striped")
                if table:
                    for row in table.find_all("tr"):
                        th = row.th.text.strip() if row.th else ""
                        td = row.td.text.strip() if row.td else ""
                        if th == "UPC":
                            book.upc = td
                        elif th == "Tax":
                            book.tax_raw = td
                        elif th == "Availability":
                            book.stock_quantity_raw = td

                # Product Description
                desc_div = soup.find("div", id="product_description")
                if desc_div:
                    p_elem = desc_div.find_next_sibling("p")
                    if p_elem:
                        book.description = p_elem.text.strip()

        except Exception as e:
            logger.debug(f"Could not enrich details for {book.book_url}: {e}")

        return book

    def scrape(
        self,
        max_pages: int = CONFIG.scraper.default_pages,
        fetch_details: bool = True,
        max_workers: int = CONFIG.scraper.default_workers
    ) -> pd.DataFrame:
        """
        Executes complete multi-page scrape with optional detail enrichment.
        """
        start_time = time.time()
        logger.info(f"Starting Scraper. Pages: 1..{max_pages} | Concurrency: {max_workers} | Details: {fetch_details}")

        all_books: List[RawBook] = []
        for page in range(1, max_pages + 1):
            page_books = self.scrape_catalog_page(page)
            all_books.extend(page_books)
            time.sleep(CONFIG.scraper.rate_limit_delay)

        logger.info(f"Catalogue traversal complete. Extracted {len(all_books)} book items.")

        if fetch_details and all_books:
            logger.info(f"Enriching {len(all_books)} items via {max_workers} concurrent threads...")
            enriched_books: List[RawBook] = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_book = {executor.submit(self.scrape_book_details, book): book for book in all_books}
                completed = 0
                total = len(all_books)
                for future in as_completed(future_to_book):
                    enriched_books.append(future.result())
                    completed += 1
                    if completed % 100 == 0 or completed == total:
                        logger.info(f"Detail enrichment progress: {completed}/{total} books ({completed/total*100:.0f}%)")
            all_books = enriched_books

        records = [b.to_dict() for b in all_books]
        df = pd.DataFrame(records)

        raw_csv_path = CONFIG.paths.raw_csv_path
        df.to_csv(raw_csv_path, index=False, encoding="utf-8")
        elapsed = round(time.time() - start_time, 2)
        logger.info(f"Raw dataset exported to {raw_csv_path} ({len(df)} rows in {elapsed}s).")
        return df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CodeAlpha Books Scraper")
    parser.add_argument("--pages", type=int, default=3, help="Pages to scrape (default: 3)")
    parser.add_argument("--no-details", action="store_true", help="Skip detail page enrichment")
    parser.add_argument("--workers", type=int, default=10, help="Worker threads")
    args = parser.parse_args()

    scraper = BooksScraper()
    df = scraper.scrape(
        max_pages=args.pages,
        fetch_details=not args.no_details,
        max_workers=args.workers
    )
    print(df.head())
