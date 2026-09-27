"""
Unit Tests for Data Cleaning Module
Validates currency parsing, rating conversion, stock extraction, and dataframe transformation.
"""

import os
import sys
import unittest
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.data_cleaner import DataCleaner


class TestDataCleaner(unittest.TestCase):
    """Test suite for DataCleaner methods."""

    def setUp(self):
        self.cleaner = DataCleaner()

    def test_clean_currency_standard(self):
        """Tests standard currency strings with pound and dollar signs."""
        self.assertEqual(self.cleaner.clean_currency("£51.77"), 51.77)
        self.assertEqual(self.cleaner.clean_currency("$19.99"), 19.99)
        self.assertEqual(self.cleaner.clean_currency("  £ 100.50  "), 100.50)

    def test_clean_currency_edge_cases(self):
        """Tests edge cases: None, empty string, non-numeric values."""
        self.assertEqual(self.cleaner.clean_currency(None), 0.0)
        self.assertEqual(self.cleaner.clean_currency(""), 0.0)
        self.assertEqual(self.cleaner.clean_currency("Free"), 0.0)
        self.assertEqual(self.cleaner.clean_currency("£0.00"), 0.0)

    def test_clean_rating_all_values(self):
        """Tests textual rating mapping from One to Five."""
        self.assertEqual(self.cleaner.clean_rating("One"), 1)
        self.assertEqual(self.cleaner.clean_rating("Two"), 2)
        self.assertEqual(self.cleaner.clean_rating("Three"), 3)
        self.assertEqual(self.cleaner.clean_rating("Four"), 4)
        self.assertEqual(self.cleaner.clean_rating("Five"), 5)

    def test_clean_rating_case_insensitivity_and_unknown(self):
        """Tests case insensitivity and unknown inputs."""
        self.assertEqual(self.cleaner.clean_rating("one"), 1)
        self.assertEqual(self.cleaner.clean_rating("FIVE"), 5)
        self.assertEqual(self.cleaner.clean_rating("Unknown"), 0)
        self.assertEqual(self.cleaner.clean_rating(None), 0)

    def test_extract_stock_quantity_regex(self):
        """Tests regex extraction of available unit counts."""
        self.assertEqual(self.cleaner.extract_stock_quantity("In stock (22 available)"), 22)
        self.assertEqual(self.cleaner.extract_stock_quantity("In stock (1 available)"), 1)
        self.assertEqual(self.cleaner.extract_stock_quantity("In stock (999 available)"), 999)

    def test_extract_stock_quantity_fallbacks(self):
        """Tests fallback logic when exact stock string is not present."""
        self.assertEqual(self.cleaner.extract_stock_quantity(None, "In stock"), 1)
        self.assertEqual(self.cleaner.extract_stock_quantity(None, "Out of stock"), 0)

    def test_clean_dataset_pipeline(self):
        """Tests end-to-end dataset transformation on mock data."""
        raw_mock = pd.DataFrame([
            {
                "title": " Test Book 1 ",
                "price_raw": "£25.00",
                "rating_str": "Four",
                "availability_raw": "In stock (10 available)",
                "book_url": "http://example.com/b1",
                "category": "Poetry",
                "stock_quantity_raw": "In stock (10 available)",
                "tax_raw": "£0.00"
            },
            {
                "title": " Test Book 2 ",
                "price_raw": "£50.00",
                "rating_str": "Two",
                "availability_raw": "In stock (5 available)",
                "book_url": "http://example.com/b2",
                "category": "Fiction",
                "stock_quantity_raw": "In stock (5 available)",
                "tax_raw": "£0.00"
            }
        ])

        df_cleaned, metrics = self.cleaner.clean_dataset(raw_mock)

        self.assertEqual(len(df_cleaned), 2)
        self.assertEqual(df_cleaned.iloc[0]["title"], "Test Book 1")
        self.assertEqual(df_cleaned.iloc[0]["price_gbp"], 25.00)
        self.assertEqual(df_cleaned.iloc[0]["rating_num"], 4)
        self.assertEqual(df_cleaned.iloc[0]["stock_quantity"], 10)
        self.assertEqual(df_cleaned.iloc[0]["inventory_value_gbp"], 250.00)
        self.assertEqual(df_cleaned.iloc[0]["price_tier"], "Mid-Range (£20-£40)")
        self.assertEqual(metrics.total_cleaned, 2)


if __name__ == "__main__":
    unittest.main()
