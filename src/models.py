"""
Data Models and Schemas
Provides typed, structured dataclasses for books and scraping metrics.
"""

from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any


@dataclass
class RawBook:
    """Represents a raw scraped book record directly from HTML."""
    title: str
    price_raw: str
    rating_str: str
    availability_raw: str
    book_url: str
    image_url: str = ""
    page_number: int = 1
    category: str = "Unknown"
    upc: str = ""
    tax_raw: str = "£0.00"
    stock_quantity_raw: str = ""
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CleanedBook:
    """Represents a fully cleaned, validated, and enriched book record."""
    title: str
    price_gbp: float
    rating_num: int
    stock_quantity: int
    in_stock: bool
    category: str
    price_tier: str
    inventory_value_gbp: float
    tax_gbp: float
    upc: str
    book_url: str
    image_url: str
    page_number: int
    description: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class PipelineMetrics:
    """Stores execution metrics for the pipeline run."""
    total_scraped: int = 0
    total_cleaned: int = 0
    duplicates_removed: int = 0
    mean_price: float = 0.0
    median_price: float = 0.0
    mean_rating: float = 0.0
    total_inventory_units: int = 0
    total_inventory_value: float = 0.0
    distinct_categories: int = 0
    elapsed_time_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
