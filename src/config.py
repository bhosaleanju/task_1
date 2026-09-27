"""
Configuration Management Module
Centralizes all application settings, URLs, directories, and parameters.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class ScraperConfig:
    """Configuration for web scraper."""
    base_url: str = "http://books.toscrape.com/"
    catalogue_url: str = "http://books.toscrape.com/catalogue/"
    total_pages: int = 50
    default_pages: int = 50
    default_workers: int = 10
    timeout_seconds: int = 15
    max_retries: int = 3
    backoff_factor: float = 0.5
    rate_limit_delay: float = 0.1
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 (CodeAlpha Data Analytics)"
    )


@dataclass(frozen=True)
class PathConfig:
    """Configuration for file system paths."""
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir: str = os.path.join(base_dir, "data")
    visualizations_dir: str = os.path.join(base_dir, "visualizations")
    reports_dir: str = os.path.join(base_dir, "reports")
    logs_dir: str = os.path.join(base_dir, "logs")

    raw_csv_path: str = os.path.join(data_dir, "raw_books_data.csv")
    cleaned_csv_path: str = os.path.join(data_dir, "cleaned_books_data.csv")
    cleaned_json_path: str = os.path.join(data_dir, "cleaned_books_data.json")
    analysis_report_path: str = os.path.join(reports_dir, "analysis_report.md")
    log_file_path: str = os.path.join(logs_dir, "pipeline.log")


@dataclass(frozen=True)
class AppConfig:
    """Master Application Configuration."""
    scraper: ScraperConfig = field(default_factory=ScraperConfig)
    paths: PathConfig = field(default_factory=PathConfig)


# Global singleton configuration instance
CONFIG = AppConfig()

# Ensure required directories exist
for directory in [
    CONFIG.paths.data_dir,
    CONFIG.paths.visualizations_dir,
    CONFIG.paths.reports_dir,
    CONFIG.paths.logs_dir
]:
    os.makedirs(directory, exist_ok=True)
