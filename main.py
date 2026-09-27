"""
CodeAlpha Data Analytics - Task 1: Web Scraping and Data Analysis Pipeline
Main entrypoint executing end-to-end data scraping, cleaning, exploratory analysis, and reporting.
"""

import os
import sys
import time
import argparse

from src.config import CONFIG
from src.logger import get_logger
from src.scraper import BooksScraper
from src.data_cleaner import DataCleaner
from src.eda_analysis import BookDataAnalyzer
from tests.run_tests import run_all_tests

logger = get_logger("MainPipeline")

BANNER = r"""
========================================================================
   ____          _        _    _       _            _____         _      _ 
  / ___|___   __| | ___  / \  | |_ __ | |__   __ _ |_   _|_ _ ___| | __ / |
 | |   / _ \ / _` |/ _ \/ _ \ | | '_ \| '_ \ / _` |  | |/ _` / __| |/ / | |
 | |__| (_) | (_| |  __/ ___ \| | |_) | | | | (_| |  | | (_| \__ \   <  | |
  \____\___/ \__,_|\___/_/   \_\_| .__/|_| |_|\__,_|  |_|\__,_|___/_|\_\ |_|
                                 |_|                                         
               DATA ANALYTICS INTERNSHIP: WEB SCRAPING & EDA
========================================================================
"""

def run_pipeline(
    pages: int = CONFIG.scraper.default_pages,
    skip_scrape: bool = False,
    fetch_details: bool = True,
    workers: int = CONFIG.scraper.default_workers
):
    """Executes end-to-end web scraping, cleaning, and analysis pipeline."""
    print(BANNER)
    start_total = time.time()

    # Step 1: Web Scraping
    if not skip_scrape:
        logger.info(f"==> STEP 1: Web Scraping (Target: {pages} pages, Details: {fetch_details})")
        scraper = BooksScraper()
        df_raw = scraper.scrape(
            max_pages=pages,
            fetch_details=fetch_details,
            max_workers=workers
        )
        logger.info(f"Scraped {len(df_raw)} records successfully.\n")
    else:
        logger.info(f"==> STEP 1: Skipping scraping step (using existing {CONFIG.paths.raw_csv_path})\n")

    # Step 2: Data Cleaning & Feature Engineering
    logger.info("==> STEP 2: Data Cleaning & Feature Engineering")
    cleaner = DataCleaner()
    df_cleaned = cleaner.clean_and_save()
    logger.info(f"Cleaned {len(df_cleaned)} records saved.\n")

    # Step 3: Exploratory Data Analysis & Visualizations
    logger.info("==> STEP 3: Exploratory Data Analysis & Visualization Generation")
    analyzer = BookDataAnalyzer()
    outputs = analyzer.run_all()
    logger.info("Generated visualization charts and reports:")
    for k, v in outputs.items():
        logger.info(f"  - {k}: {v}")

    elapsed = round(time.time() - start_total, 2)
    print("\n" + "=" * 72)
    print(f"PIPELINE COMPLETED SUCCESSFULLY IN {elapsed}s!")
    print(f"Cleaned Dataset: {CONFIG.paths.cleaned_csv_path} ({len(df_cleaned)} rows)")
    print(f"Visualizations:  {CONFIG.paths.visualizations_dir}/*.png")
    print(f"Report:          {CONFIG.paths.analysis_report_path}")
    print("To launch the interactive dashboard, run:  streamlit run app.py")
    print("=" * 72 + "\n")


def main():
    parser = argparse.ArgumentParser(description="CodeAlpha Task 1 - Web Scraping Pipeline")
    parser.add_argument(
        "--pages",
        type=int,
        default=CONFIG.scraper.default_pages,
        help=f"Number of pages to scrape (1 to 50, default: {CONFIG.scraper.default_pages})"
    )
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Skip web scraping and use existing raw data"
    )
    parser.add_argument(
        "--no-details",
        action="store_true",
        help="Skip fetching individual detail pages for faster scraping"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=CONFIG.scraper.default_workers,
        help=f"Number of concurrent worker threads (default: {CONFIG.scraper.default_workers})"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run the automated test suite before executing the pipeline"
    )

    args = parser.parse_args()

    if args.test:
        logger.info("Running automated test suite...")
        run_all_tests()

    run_pipeline(
        pages=args.pages,
        skip_scrape=args.skip_scrape,
        fetch_details=not args.no_details,
        workers=args.workers
    )


if __name__ == "__main__":
    main()
