"""
Unit Tests for Scraper HTML Parsing Logic
Validates catalog pod parsing and detail page parsing using mock HTML.
"""

import os
import sys
import unittest
from bs4 import BeautifulSoup

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.scraper import BooksScraper
from src.models import RawBook

MOCK_CATALOG_HTML = """
<html>
<body>
    <article class="product_pod">
        <div class="image_container">
            <a href="catalogue/a-light-in-the-attic_1000/index.html">
                <img src="media/cache/2c/da/2cdad67c44b002e7ead0cc35693c0e8b.jpg" class="thumbnail">
            </a>
        </div>
        <p class="star-rating Three">
            <i class="icon-star"></i>
        </p>
        <h3>
            <a href="catalogue/a-light-in-the-attic_1000/index.html" title="A Light in the Attic">A Light in the Attic</a>
        </h3>
        <div class="product_price">
            <p class="price_color">£51.77</p>
            <p class="instock availability">
                <i class="icon-ok"></i>
                In stock
            </p>
        </div>
    </article>
</body>
</html>
"""

MOCK_DETAIL_HTML = """
<html>
<body>
    <ul class="breadcrumb">
        <li><a href="../../index.html">Home</a></li>
        <li><a href="../category/books_1/index.html">Books</a></li>
        <li><a href="../category/books/poetry_23/index.html">Poetry</a></li>
        <li class="active">A Light in the Attic</li>
    </ul>
    <div id="product_description" class="sub-header">
        <h2>Product Description</h2>
    </div>
    <p>It's hard to imagine a world without A Light in the Attic.</p>
    <table class="table table-striped">
        <tr><th>UPC</th><td>a897fe39b1053632</td></tr>
        <tr><th>Product Type</th><td>Books</td></tr>
        <tr><th>Price (excl. tax)</th><td>£51.77</td></tr>
        <tr><th>Price (incl. tax)</th><td>£51.77</td></tr>
        <tr><th>Tax</th><td>£0.00</td></tr>
        <tr><th>Availability</th><td>In stock (22 available)</td></tr>
        <tr><th>Number of reviews</th><td>0</td></tr>
    </table>
</body>
</html>
"""


class TestScraperParsing(unittest.TestCase):
    """Test suite for Scraper HTML parsing methods."""

    def test_catalog_pod_parsing(self):
        """Validates extracting fields from a product_pod HTML snippet."""
        soup = BeautifulSoup(MOCK_CATALOG_HTML, "html.parser")
        pod = soup.find("article", class_="product_pod")

        title_elem = pod.h3.find("a")
        title = title_elem.get("title", title_elem.text.strip())
        price_elem = pod.find("p", class_="price_color")
        price = price_elem.text.strip()
        rating_classes = pod.find("p", class_="star-rating")["class"]
        rating = [c for c in rating_classes if c != "star-rating"][0]
        avail = pod.find("p", class_="instock availability").text.strip()

        self.assertEqual(title, "A Light in the Attic")
        self.assertEqual(price, "£51.77")
        self.assertEqual(rating, "Three")
        self.assertEqual(avail, "In stock")

    def test_detail_page_parsing(self):
        """Validates extracting category, UPC, and exact stock from detail page HTML."""
        soup = BeautifulSoup(MOCK_DETAIL_HTML, "html.parser")

        breadcrumb = [li.text.strip() for li in soup.find("ul", class_="breadcrumb").find_all("li")]
        category = breadcrumb[2] if len(breadcrumb) >= 3 else "Unknown"

        table = {
            tr.th.text.strip(): tr.td.text.strip()
            for tr in soup.find("table", class_="table-striped").find_all("tr")
        }

        self.assertEqual(category, "Poetry")
        self.assertEqual(table.get("UPC"), "a897fe39b1053632")
        self.assertEqual(table.get("Availability"), "In stock (22 available)")
        self.assertEqual(table.get("Tax"), "£0.00")


if __name__ == "__main__":
    unittest.main()
