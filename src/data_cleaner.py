"""
Data Cleaning and Feature Engineering Module
Transforms raw scraped book data into structured, validated analytical datasets.
"""

import os
import re
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np

from src.config import CONFIG
from src.logger import get_logger
from src.models import PipelineMetrics
from src.exceptions import DataCleaningError

logger = get_logger("DataCleaner")


class DataCleaner:
    """
    Transforms raw scraped records:
    - Normalizes currency and formats prices as float64
    - Translates star ratings from text strings to 1-5 integers
    - Regex extracts stock counts from availability strings
    - Categorizes items into business price tiers (Budget, Mid-Range, Premium)
    - Computes total inventory valuations
    - Enforces deduplication and schema consistency
    """

    RATING_MAP = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5
    }

    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = data_dir or CONFIG.paths.data_dir

    @staticmethod
    def clean_currency(val: Any) -> float:
        """Strips currency symbols (£, $, whitespace) and parses float."""
        if pd.isna(val) or val is None:
            return 0.0
        val_str = str(val).strip()
        cleaned = re.sub(r"[^\d.]", "", val_str)
        try:
            return float(cleaned) if cleaned else 0.0
        except ValueError:
            return 0.0

    @classmethod
    def clean_rating(cls, val: Any) -> int:
        """Converts textual star rating to integer between 1 and 5."""
        if pd.isna(val) or val is None:
            return 0
        val_str = str(val).strip().lower()
        return cls.RATING_MAP.get(val_str, 0)

    @staticmethod
    def extract_stock_quantity(stock_str: Any, availability_raw: Any = "") -> int:
        """Extracts available integer count from 'In stock (22 available)' string."""
        if pd.notna(stock_str) and str(stock_str).strip():
            match = re.search(r"\((\d+)\s*available\)", str(stock_str), re.IGNORECASE)
            if match:
                return int(match.group(1))

        if pd.notna(availability_raw):
            avail_lower = str(availability_raw).lower()
            if "in stock" in avail_lower:
                match = re.search(r"\d+", avail_lower)
                return int(match.group(0)) if match else 1
            if "out of stock" in avail_lower:
                return 0

        return 0

    def clean_dataset(self, df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, PipelineMetrics]:
        """
        Executes complete cleaning and feature engineering pipeline on a DataFrame.
        """
        if df_raw.empty:
            raise DataCleaningError("Input DataFrame is empty. Cannot perform cleaning.")

        logger.info(f"Starting data transformation pipeline on {len(df_raw)} records...")
        df = df_raw.copy()

        # 1. Clean Title
        df["title"] = df["title"].astype(str).str.strip()

        # 2. Clean Prices
        df["price_gbp"] = df["price_raw"].apply(self.clean_currency)
        if "tax_raw" in df.columns:
            df["tax_gbp"] = df["tax_raw"].apply(self.clean_currency)
        else:
            df["tax_gbp"] = 0.0

        # 3. Clean Ratings
        df["rating_num"] = df["rating_str"].apply(self.clean_rating)

        # 4. Clean Stock & Availability
        df["stock_quantity"] = [
            self.extract_stock_quantity(s, a)
            for s, a in zip(
                df.get("stock_quantity_raw", [None] * len(df)),
                df.get("availability_raw", [None] * len(df))
            )
        ]
        df["in_stock"] = df["stock_quantity"] > 0

        # 5. Standardize Category
        if "category" in df.columns:
            df["category"] = df["category"].fillna("Unknown").astype(str).str.strip()
            df["category"] = df["category"].apply(lambda x: "General" if x in ("", "Unknown") else x)
        else:
            df["category"] = "General"

        # 6. Feature Engineering: Total Inventory Value
        df["inventory_value_gbp"] = (df["price_gbp"] * df["stock_quantity"]).round(2)

        # 7. Price Segments for Business Analytics
        df["price_tier"] = pd.cut(
            df["price_gbp"],
            bins=[0, 20, 40, float("inf")],
            labels=["Budget (<£20)", "Mid-Range (£20-£40)", "Premium (>£40)"],
            right=False
        )

        # 8. Deduplication
        initial_count = len(df)
        if "book_url" in df.columns:
            df = df.drop_duplicates(subset=["book_url"])
        else:
            df = df.drop_duplicates(subset=["title"])
        duplicates_removed = initial_count - len(df)

        metrics = PipelineMetrics(
            total_scraped=initial_count,
            total_cleaned=len(df),
            duplicates_removed=duplicates_removed,
            mean_price=round(float(df["price_gbp"].mean()), 2),
            median_price=round(float(df["price_gbp"].median()), 2),
            mean_rating=round(float(df["rating_num"].mean()), 2),
            total_inventory_units=int(df["stock_quantity"].sum()),
            total_inventory_value=round(float(df["inventory_value_gbp"].sum()), 2),
            distinct_categories=int(df["category"].nunique())
        )

        logger.info(
            f"Cleaning completed: {len(df)} records | "
            f"Mean Price: £{metrics.mean_price} | "
            f"Mean Rating: {metrics.mean_rating}/5 | "
            f"Stock Units: {metrics.total_inventory_units:,}"
        )
        return df, metrics

    def clean_and_save(
        self,
        raw_csv_path: Optional[str] = None,
        cleaned_csv_path: Optional[str] = None,
        cleaned_json_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Loads raw data file, processes it, and writes clean CSV and JSON outputs.
        """
        raw_path = raw_csv_path or CONFIG.paths.raw_csv_path
        clean_csv = cleaned_csv_path or CONFIG.paths.cleaned_csv_path
        clean_json = cleaned_json_path or CONFIG.paths.cleaned_json_path

        if not os.path.exists(raw_path):
            raise FileNotFoundError(f"Raw data file not found at: {raw_path}")

        df_raw = pd.read_csv(raw_path)
        df_cleaned, metrics = self.clean_dataset(df_raw)

        os.makedirs(os.path.dirname(clean_csv), exist_ok=True)
        df_cleaned.to_csv(clean_csv, index=False, encoding="utf-8")
        df_cleaned.to_json(clean_json, orient="records", indent=2)

        logger.info(f"Cleaned dataset written to:\n  - CSV: {clean_csv}\n  - JSON: {clean_json}")
        return df_cleaned


if __name__ == "__main__":
    cleaner = DataCleaner()
    df = cleaner.clean_and_save()
    print(df.head())
