"""
Configuration management for AI Crypto News
Centralizes all configuration, API keys, and constants
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
DATA_DIR = BASE_DIR / "data"
SITE_DIR = BASE_DIR / "site"
CONTENT_DIR = SITE_DIR / "content" / "news"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CONTENT_DIR.mkdir(parents=True, exist_ok=True)

# API Configuration
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"
COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")  # Optional

GNEWS_API_BASE = "https://gnews.io/api/v4"
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")

# Cryptocurrency settings
TOP_N_COINS = int(os.getenv("TOP_N_COINS", "100"))
MAX_ARTICLES_PER_RUN = int(os.getenv("MAX_ARTICLES_PER_RUN", "100"))

# Content settings
DAYS_TO_KEEP = int(os.getenv("DAYS_TO_KEEP", "30"))

# Hugo settings
BASE_URL = os.getenv("BASE_URL", "https://yourusername.github.io/ai-crypto-news/")
HUGO_ENV = os.getenv("HUGO_ENV", "production")

# File paths
COINS_JSON_PATH = DATA_DIR / "coins.json"
NEWS_CACHE_PATH = DATA_DIR / "news_cache.json"

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# API rate limiting
COINGECKO_RATE_LIMIT = 10  # calls per minute (free tier: 10-30)
GNEWS_DAILY_LIMIT = 100  # requests per day

# News fetching settings
NEWS_LANGUAGE = "en"
NEWS_COUNTRY = "us"
NEWS_MAX_PER_QUERY = 100  # Max articles per GNews request

# Top coins to prioritize in search query (use top 20 for aggregated search)
TOP_PRIORITY_COINS = 20

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "2000"))

# Scraping Configuration
SCRAPE_TIMEOUT = 15  # seconds
SCRAPE_DELAY = 2  # seconds between requests
USER_AGENT = "Mozilla/5.0 (compatible; CryptoNewsBot/1.0)"
