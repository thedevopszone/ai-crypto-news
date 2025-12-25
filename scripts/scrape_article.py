"""
Scrape full article content from URLs using newspaper3k
"""

import time
from newspaper import Article
from bs4 import BeautifulSoup
import requests

from config import SCRAPE_TIMEOUT, SCRAPE_DELAY, USER_AGENT
from utils import setup_logger

logger = setup_logger(__name__)


def scrape_article_content(url):
    """
    Scrape full article content from URL

    Args:
        url: Article URL to scrape

    Returns:
        Dict with 'title', 'text', 'authors', 'publish_date' or None if failed
    """
    try:
        logger.info(f"Scraping article: {url}")

        # Use newspaper3k to extract article
        article = Article(url)
        article.config.browser_user_agent = USER_AGENT
        article.config.request_timeout = SCRAPE_TIMEOUT

        # Download and parse
        article.download()
        article.parse()

        # Extract content
        if article.text and len(article.text) > 200:
            result = {
                'title': article.title,
                'text': article.text,
                'authors': article.authors,
                'publish_date': article.publish_date
            }

            logger.info(f"Successfully scraped {len(article.text)} characters")
            return result
        else:
            logger.warning(f"Article text too short or empty: {url}")
            return None

    except Exception as e:
        logger.error(f"Scraping failed for {url}: {e}")

        # Fallback to BeautifulSoup
        try:
            return scrape_with_beautifulsoup(url)
        except Exception as fallback_error:
            logger.error(f"BeautifulSoup fallback also failed: {fallback_error}")
            return None


def scrape_with_beautifulsoup(url):
    """
    Fallback scraper using BeautifulSoup

    Args:
        url: Article URL

    Returns:
        Dict with article content or None
    """
    logger.info(f"Trying BeautifulSoup fallback for: {url}")

    headers = {'User-Agent': USER_AGENT}
    response = requests.get(url, headers=headers, timeout=SCRAPE_TIMEOUT)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'lxml')

    # Try to find article content
    # Common selectors for article content
    article_selectors = [
        'article',
        '.article-content',
        '.post-content',
        '.entry-content',
        'main',
        '.content'
    ]

    text = ""
    for selector in article_selectors:
        content = soup.select_one(selector)
        if content:
            # Get all paragraph text
            paragraphs = content.find_all('p')
            text = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            if len(text) > 200:
                break

    if len(text) > 200:
        # Try to get title
        title = ""
        title_tag = soup.find('h1') or soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()

        result = {
            'title': title,
            'text': text,
            'authors': [],
            'publish_date': None
        }

        logger.info(f"BeautifulSoup extracted {len(text)} characters")
        return result
    else:
        logger.warning(f"Could not extract enough text with BeautifulSoup")
        return None


def is_scrapable(url):
    """
    Check if URL is accessible and scrapable

    Args:
        url: URL to check

    Returns:
        True if scrapable, False otherwise
    """
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"URL not accessible: {url} - {e}")
        return False


def rate_limit_delay():
    """
    Add delay between scraping requests to be respectful
    """
    time.sleep(SCRAPE_DELAY)


def main():
    """
    Test scraping functionality
    """
    test_url = "https://coingape.com/bitcoin-ai-coins-bounce-as-nvidia-signs-20b-ai-inference-deal-with-groq/"

    logger.info("Testing article scraper...")

    if is_scrapable(test_url):
        content = scrape_article_content(test_url)
        if content:
            logger.info(f"Title: {content['title']}")
            logger.info(f"Text length: {len(content['text'])} characters")
            logger.info(f"First 200 chars: {content['text'][:200]}...")
        else:
            logger.error("Failed to scrape content")
    else:
        logger.error("URL not scrapable")


if __name__ == "__main__":
    main()
