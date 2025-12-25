"""
Fetch cryptocurrency news from GNews API
Uses aggregated search strategy to stay within API limits
"""

import json
import requests
from datetime import datetime, timedelta
import pytz

from config import (
    GNEWS_API_BASE,
    GNEWS_API_KEY,
    NEWS_LANGUAGE,
    NEWS_COUNTRY,
    NEWS_MAX_PER_QUERY,
    TOP_PRIORITY_COINS,
    MAX_ARTICLES_PER_RUN
)
from utils import setup_logger, retry_with_backoff, match_coin_in_text, calculate_relevance_score
from fetch_coins import load_coins

logger = setup_logger(__name__)


@retry_with_backoff(max_retries=3, base_delay=2)
def fetch_news_from_gnews(query, max_articles=100):
    """
    Fetch news from GNews API

    Args:
        query: Search query string
        max_articles: Maximum number of articles to fetch

    Returns:
        List of article dicts
    """
    logger.info(f"Fetching news from GNews with query: {query[:100]}...")

    if not GNEWS_API_KEY:
        raise ValueError("GNEWS_API_KEY is not set in environment variables")

    url = f"{GNEWS_API_BASE}/search"

    # Get articles from last 24 hours
    to_date = datetime.now(pytz.UTC)
    from_date = to_date - timedelta(days=1)

    params = {
        "q": query,
        "lang": NEWS_LANGUAGE,
        "country": NEWS_COUNTRY,
        "max": min(max_articles, NEWS_MAX_PER_QUERY),
        "apikey": GNEWS_API_KEY,
        "from": from_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "to": to_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    articles = data.get("articles", [])

    logger.info(f"Fetched {len(articles)} articles from GNews")

    return articles


def build_aggregated_query(coins, top_n=TOP_PRIORITY_COINS):
    """
    Build an aggregated search query with OR logic for top coins

    Args:
        coins: List of coin dicts
        top_n: Number of top coins to include in query

    Returns:
        Search query string
    """
    # Get top N coins by market cap rank
    top_coins = sorted(coins, key=lambda c: c.get('market_cap_rank', 999))[:top_n]

    # Build OR query with coin names
    terms = []

    # Add general crypto terms
    terms.extend(["cryptocurrency", "crypto", "bitcoin"])

    # Add top coin names (avoid duplicates)
    seen = set(["bitcoin"])  # Bitcoin already added above
    for coin in top_coins:
        name = coin['name']
        if name.lower() not in seen:
            terms.append(name)
            seen.add(name.lower())

    # Join with OR (GNews supports OR operator)
    query = " OR ".join(terms)

    logger.info(f"Built query with {len(terms)} terms for top {top_n} coins")

    return query


def match_articles_to_coins(articles, coins):
    """
    Match articles to specific coins based on content

    Args:
        articles: List of article dicts from GNews
        coins: List of coin dicts

    Returns:
        List of enriched article dicts with 'coins' field
    """
    logger.info(f"Matching {len(articles)} articles to {len(coins)} coins...")

    enriched_articles = []

    for article in articles:
        # Combine title and description for matching
        text = f"{article.get('title', '')} {article.get('description', '')}"

        # Find matching coins
        matched_coins = []
        coin_scores = []

        for coin in coins:
            if match_coin_in_text(text, coin):
                score = calculate_relevance_score(article, coin)
                matched_coins.append({
                    'id': coin['id'],
                    'symbol': coin['symbol'],
                    'name': coin['name']
                })
                coin_scores.append(score)

        # Only include articles that match at least one coin
        if matched_coins:
            # Sort matched coins by relevance score
            sorted_coins = [coin for _, coin in sorted(
                zip(coin_scores, matched_coins),
                key=lambda x: x[0],
                reverse=True
            )]

            enriched_articles.append({
                'title': article.get('title'),
                'description': article.get('description'),
                'url': article.get('url'),
                'image': article.get('image'),
                'publishedAt': article.get('publishedAt'),
                'source': {
                    'name': article.get('source', {}).get('name'),
                    'url': article.get('source', {}).get('url')
                },
                'coins': sorted_coins,  # List of matched coins, sorted by relevance
                'content': article.get('content', '')
            })

    logger.info(f"Matched {len(enriched_articles)} articles to coins")

    return enriched_articles


def deduplicate_articles(articles):
    """
    Remove duplicate articles based on URL

    Args:
        articles: List of article dicts

    Returns:
        Deduplicated list of articles
    """
    seen_urls = set()
    unique_articles = []

    for article in articles:
        url = article.get('url')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_articles.append(article)

    if len(articles) != len(unique_articles):
        logger.info(f"Removed {len(articles) - len(unique_articles)} duplicate articles")

    return unique_articles


def fetch_crypto_news(coins=None):
    """
    Main function to fetch cryptocurrency news

    Args:
        coins: List of coin dicts (if None, will load from file)

    Returns:
        List of enriched article dicts with coin matching
    """
    if coins is None:
        coins = load_coins()
        if not coins:
            raise ValueError("No coins data available. Run fetch_coins.py first.")

    # Build aggregated search query
    query = build_aggregated_query(coins)

    # Fetch news from GNews (uses 1 API request)
    articles = fetch_news_from_gnews(query, max_articles=MAX_ARTICLES_PER_RUN)

    if not articles:
        logger.warning("No articles fetched from GNews")
        return []

    # Match articles to specific coins
    enriched_articles = match_articles_to_coins(articles, coins)

    # Remove duplicates
    unique_articles = deduplicate_articles(enriched_articles)

    # Limit to max articles
    if len(unique_articles) > MAX_ARTICLES_PER_RUN:
        unique_articles = unique_articles[:MAX_ARTICLES_PER_RUN]
        logger.info(f"Limited articles to {MAX_ARTICLES_PER_RUN}")

    logger.info(f"Final article count: {len(unique_articles)}")

    return unique_articles


def main():
    """
    Main function for standalone execution
    """
    try:
        articles = fetch_crypto_news()

        logger.info(f"Fetched {len(articles)} unique crypto news articles")

        if articles:
            # Show sample
            sample = articles[0]
            logger.info(f"Sample article: {sample['title']}")
            logger.info(f"Coins: {', '.join([c['name'] for c in sample['coins']])}")
            logger.info(f"Source: {sample['source']['name']}")

        return articles

    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        raise


if __name__ == "__main__":
    main()
