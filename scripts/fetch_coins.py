"""
Fetch top 100 cryptocurrencies from CoinGecko API
"""

import json
import requests

from config import (
    COINGECKO_API_BASE,
    COINGECKO_API_KEY,
    TOP_N_COINS,
    COINS_JSON_PATH,
    COINGECKO_RATE_LIMIT
)
from utils import setup_logger, retry_with_backoff, rate_limit

logger = setup_logger(__name__)


@retry_with_backoff(max_retries=3, base_delay=2)
@rate_limit(calls_per_minute=COINGECKO_RATE_LIMIT)
def fetch_top_coins():
    """
    Fetch top N cryptocurrencies by market cap from CoinGecko

    Returns:
        List of coin dicts with id, symbol, name, market_cap_rank
    """
    logger.info(f"Fetching top {TOP_N_COINS} cryptocurrencies from CoinGecko...")

    url = f"{COINGECKO_API_BASE}/coins/markets"

    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": TOP_N_COINS,
        "page": 1,
        "sparkline": False,
        "locale": "en"
    }

    headers = {}
    if COINGECKO_API_KEY:
        headers["x-cg-pro-api-key"] = COINGECKO_API_KEY

    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()

    coins_data = response.json()

    # Extract relevant fields
    coins = []
    for coin in coins_data:
        coins.append({
            "id": coin.get("id"),
            "symbol": coin.get("symbol"),
            "name": coin.get("name"),
            "market_cap_rank": coin.get("market_cap_rank")
        })

    logger.info(f"Successfully fetched {len(coins)} coins")

    return coins


def save_coins(coins):
    """
    Save coins data to JSON file

    Args:
        coins: List of coin dicts
    """
    logger.info(f"Saving coins to {COINS_JSON_PATH}")

    with open(COINS_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(coins, f, indent=2, ensure_ascii=False)

    logger.info("Coins saved successfully")


def load_coins():
    """
    Load coins data from JSON file

    Returns:
        List of coin dicts, or None if file doesn't exist
    """
    if not COINS_JSON_PATH.exists():
        logger.warning(f"Coins file not found: {COINS_JSON_PATH}")
        return None

    logger.info(f"Loading coins from {COINS_JSON_PATH}")

    with open(COINS_JSON_PATH, 'r', encoding='utf-8') as f:
        coins = json.load(f)

    logger.info(f"Loaded {len(coins)} coins")

    return coins


def main():
    """
    Main function to fetch and save top coins
    """
    try:
        coins = fetch_top_coins()
        save_coins(coins)

        logger.info(f"Top 10 coins: {', '.join([c['name'] for c in coins[:10]])}")

        return coins

    except Exception as e:
        logger.error(f"Error fetching coins: {e}")
        raise


if __name__ == "__main__":
    main()
