#!/usr/bin/env python3
"""
Main orchestrator for daily crypto news update
Runs all steps in sequence: fetch coins, fetch news, generate content
"""

import sys
from datetime import datetime
import pytz

from utils import setup_logger
from fetch_coins import fetch_top_coins, save_coins, load_coins
from fetch_news import fetch_crypto_news
from generate_content import generate_content_from_articles, cleanup_old_articles

logger = setup_logger(__name__)


def print_summary(coins_count, articles_count, files_generated):
    """
    Print summary of daily run

    Args:
        coins_count: Number of coins fetched
        articles_count: Number of articles fetched
        files_generated: Number of markdown files generated
    """
    logger.info("=" * 60)
    logger.info("DAILY RUN SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Coins fetched: {coins_count}")
    logger.info(f"Articles fetched: {articles_count}")
    logger.info(f"New content files generated: {files_generated}")
    logger.info(f"Completed at: {datetime.now(pytz.UTC).isoformat()}")
    logger.info("=" * 60)


def main():
    """
    Main orchestrator function
    """
    start_time = datetime.now(pytz.UTC)
    logger.info("=" * 60)
    logger.info("Starting daily crypto news update")
    logger.info(f"Start time: {start_time.isoformat()}")
    logger.info("=" * 60)

    coins = None
    articles = None
    generated_files = []

    try:
        # Step 1: Fetch top 100 coins from CoinGecko
        logger.info("\n[Step 1/4] Fetching top 100 cryptocurrencies...")
        coins = fetch_top_coins()
        save_coins(coins)
        logger.info(f"✓ Successfully fetched {len(coins)} coins")

    except Exception as e:
        logger.error(f"✗ Failed to fetch coins: {e}")
        logger.warning("Attempting to load cached coins...")
        coins = load_coins()

        if not coins:
            logger.error("No cached coins available. Cannot continue.")
            sys.exit(1)

        logger.info(f"✓ Loaded {len(coins)} coins from cache")

    try:
        # Step 2: Fetch crypto news from GNews API
        logger.info("\n[Step 2/4] Fetching cryptocurrency news...")
        articles = fetch_crypto_news(coins)
        logger.info(f"✓ Successfully fetched {len(articles)} articles")

        if not articles:
            logger.warning("No articles fetched. This may be normal if no news is available.")

    except Exception as e:
        logger.error(f"✗ Failed to fetch news: {e}")
        articles = []

    try:
        # Step 3: Generate Hugo content files
        logger.info("\n[Step 3/4] Generating Hugo content files...")

        if articles:
            generated_files = generate_content_from_articles(articles)
            logger.info(f"✓ Generated {len(generated_files)} new content files")
        else:
            logger.warning("No articles to generate content from")

    except Exception as e:
        logger.error(f"✗ Failed to generate content: {e}")

    try:
        # Step 4: Clean up old articles
        logger.info("\n[Step 4/4] Cleaning up old articles...")
        cleanup_old_articles()
        logger.info("✓ Cleanup complete")

    except Exception as e:
        logger.error(f"✗ Failed to cleanup old articles: {e}")

    # Print summary
    end_time = datetime.now(pytz.UTC)
    duration = (end_time - start_time).total_seconds()

    logger.info("")
    print_summary(
        coins_count=len(coins) if coins else 0,
        articles_count=len(articles) if articles else 0,
        files_generated=len(generated_files)
    )
    logger.info(f"Total duration: {duration:.2f} seconds")

    # Return success if we got at least some data
    if coins:
        logger.info("\n✓ Daily update completed successfully")
        sys.exit(0)
    else:
        logger.error("\n✗ Daily update failed")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\nDaily update interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Unexpected error in daily update: {e}")
        sys.exit(1)
