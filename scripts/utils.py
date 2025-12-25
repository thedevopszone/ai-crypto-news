"""
Utility functions for AI Crypto News
Provides helper functions for logging, sanitization, and retry logic
"""

import re
import logging
import time
from functools import wraps
from datetime import datetime
import pytz

from config import LOG_LEVEL, LOG_FORMAT


def setup_logger(name):
    """
    Set up a logger with consistent formatting

    Args:
        name: Logger name (usually __name__ of the module)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)

    return logger


def sanitize_filename(text, max_length=100):
    """
    Sanitize a string for use in filenames

    Args:
        text: Input text to sanitize
        max_length: Maximum length of the resulting filename

    Returns:
        Sanitized filename string
    """
    # Convert to lowercase
    text = text.lower()

    # Remove special characters, keep alphanumeric and spaces
    text = re.sub(r'[^a-z0-9\s-]', '', text)

    # Replace spaces with hyphens
    text = re.sub(r'\s+', '-', text)

    # Remove multiple consecutive hyphens
    text = re.sub(r'-+', '-', text)

    # Strip leading/trailing hyphens
    text = text.strip('-')

    # Limit length
    if len(text) > max_length:
        text = text[:max_length].rstrip('-')

    return text


def retry_with_backoff(max_retries=3, base_delay=1, backoff_factor=2):
    """
    Decorator to retry a function with exponential backoff

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        backoff_factor: Multiplier for delay on each retry

    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"{func.__name__} failed after {max_retries} attempts: {e}")
                        raise

                    delay = base_delay * (backoff_factor ** attempt)
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)

        return wrapper
    return decorator


def format_datetime_iso(dt_string):
    """
    Convert various datetime formats to ISO format for Hugo

    Args:
        dt_string: Input datetime string

    Returns:
        ISO formatted datetime string
    """
    try:
        # Try parsing ISO format first
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        try:
            # Try parsing RFC 2822 format (common in RSS)
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(dt_string)
        except Exception:
            # Default to current time if parsing fails
            dt = datetime.now(pytz.UTC)

    # Ensure timezone aware
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)

    return dt.isoformat()


def get_current_time_utc():
    """
    Get current time in UTC as ISO string

    Returns:
        Current UTC time in ISO format
    """
    return datetime.now(pytz.UTC).isoformat()


def match_coin_in_text(text, coin_data):
    """
    Check if a coin is mentioned in text

    Args:
        text: Text to search in (lowercase)
        coin_data: Dict with 'id', 'symbol', 'name' keys

    Returns:
        Boolean indicating if coin is mentioned
    """
    if not text:
        return False

    text_lower = text.lower()

    # Check for exact name match
    if coin_data['name'].lower() in text_lower:
        return True

    # Check for symbol match (as whole word)
    symbol_pattern = r'\b' + re.escape(coin_data['symbol'].lower()) + r'\b'
    if re.search(symbol_pattern, text_lower):
        return True

    # Check for ID match (e.g., "bitcoin" for Bitcoin)
    if coin_data['id'].lower() in text_lower:
        return True

    return False


def calculate_relevance_score(article, coin_data):
    """
    Calculate relevance score for an article-coin match

    Args:
        article: Article dict with 'title' and 'description'
        coin_data: Coin dict with 'id', 'symbol', 'name'

    Returns:
        Float relevance score (higher is more relevant)
    """
    score = 0.0

    title = (article.get('title') or '').lower()
    description = (article.get('description') or '').lower()

    coin_name = coin_data['name'].lower()
    coin_symbol = coin_data['symbol'].lower()
    coin_id = coin_data['id'].lower()

    # Title matches are worth more
    if coin_name in title:
        score += 10.0
    if coin_symbol in title:
        score += 8.0
    if coin_id in title:
        score += 6.0

    # Description matches
    if coin_name in description:
        score += 5.0
    if coin_symbol in description:
        score += 4.0
    if coin_id in description:
        score += 3.0

    return score


def truncate_text(text, max_length=200, suffix='...'):
    """
    Truncate text to a maximum length

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text

    # Try to truncate at a word boundary
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')

    if last_space > 0:
        truncated = truncated[:last_space]

    return truncated + suffix


def rate_limit(calls_per_minute):
    """
    Decorator to enforce rate limiting

    Args:
        calls_per_minute: Maximum number of calls allowed per minute

    Returns:
        Decorated function
    """
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed

            if left_to_wait > 0:
                time.sleep(left_to_wait)

            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret

        return wrapper
    return decorator
