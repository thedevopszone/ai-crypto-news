"""
Generate Hugo markdown content from news articles
"""

import os
import yaml
from datetime import datetime, timedelta
from pathlib import Path
import pytz

from config import CONTENT_DIR, DAYS_TO_KEEP
from utils import setup_logger, sanitize_filename, format_datetime_iso

logger = setup_logger(__name__)


def generate_front_matter(article):
    """
    Generate Hugo front matter for an article

    Args:
        article: Article dict with metadata

    Returns:
        Dict of front matter data
    """
    # Extract coin symbols and IDs
    coin_symbols = [coin['symbol'] for coin in article.get('coins', [])]
    coin_names = [coin['name'] for coin in article.get('coins', [])]

    # Format datetime
    published_at = format_datetime_iso(article.get('publishedAt', ''))

    front_matter = {
        'title': article.get('title', 'Untitled'),
        'date': published_at,
        'publishDate': published_at,
        'source': article.get('source', {}).get('name', 'Unknown'),
        'sourceUrl': article.get('url', ''),
        'coins': coin_symbols,
        'coinNames': coin_names,
        'image': article.get('image', ''),
        'description': article.get('description', ''),
    }

    return front_matter


def generate_article_filename(article):
    """
    Generate filename for article markdown file

    Args:
        article: Article dict

    Returns:
        Filename string (YYYY-MM-DD-slug.md)
    """
    # Parse date
    try:
        dt = datetime.fromisoformat(
            article.get('publishedAt', '').replace('Z', '+00:00')
        )
    except (ValueError, AttributeError):
        dt = datetime.now(pytz.UTC)

    date_str = dt.strftime('%Y-%m-%d')

    # Generate slug from title
    title = article.get('title', 'untitled')
    slug = sanitize_filename(title, max_length=80)

    # Combine date and slug
    filename = f"{date_str}-{slug}.md"

    return filename


def generate_article_content(article):
    """
    Generate full markdown content for an article

    Args:
        article: Article dict

    Returns:
        Full markdown content string
    """
    # Generate front matter
    front_matter = generate_front_matter(article)

    # Convert front matter to YAML
    yaml_str = yaml.dump(front_matter, default_flow_style=False, allow_unicode=True)

    # Build markdown content
    content_parts = []
    content_parts.append('---')
    content_parts.append(yaml_str.strip())
    content_parts.append('---')
    content_parts.append('')

    # Add article description/content
    description = article.get('description', '')
    if description:
        content_parts.append(description)
        content_parts.append('')

    # Add content if available
    content = article.get('content', '')
    if content and content != description:
        content_parts.append(content)
        content_parts.append('')

    # Add link to original article
    source_url = article.get('url', '')
    source_name = article.get('source', {}).get('name', 'source')
    if source_url:
        content_parts.append(f"[Read full article on {source_name}]({source_url})")
        content_parts.append('')

    # Add coin tags
    coins = article.get('coins', [])
    if coins:
        coin_list = ', '.join([f"**{coin['name']}** ({coin['symbol'].upper()})" for coin in coins])
        content_parts.append(f"**Related Coins:** {coin_list}")
        content_parts.append('')

    return '\n'.join(content_parts)


def write_article_file(article, filename):
    """
    Write article to markdown file

    Args:
        article: Article dict
        filename: Filename to write to

    Returns:
        Path to written file
    """
    filepath = CONTENT_DIR / filename

    # Generate content
    content = generate_article_content(article)

    # Write file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    logger.debug(f"Wrote article: {filename}")

    return filepath


def cleanup_old_articles(days_to_keep=DAYS_TO_KEEP):
    """
    Remove articles older than specified days

    Args:
        days_to_keep: Number of days of articles to keep
    """
    logger.info(f"Cleaning up articles older than {days_to_keep} days...")

    if not CONTENT_DIR.exists():
        logger.warning(f"Content directory doesn't exist: {CONTENT_DIR}")
        return

    cutoff_date = datetime.now(pytz.UTC) - timedelta(days=days_to_keep)
    removed_count = 0

    for filepath in CONTENT_DIR.glob('*.md'):
        # Extract date from filename (YYYY-MM-DD-slug.md)
        try:
            date_str = filepath.name[:10]  # First 10 characters
            file_date = datetime.strptime(date_str, '%Y-%m-%d')
            file_date = pytz.UTC.localize(file_date)

            if file_date < cutoff_date:
                filepath.unlink()
                removed_count += 1
                logger.debug(f"Removed old article: {filepath.name}")

        except (ValueError, IndexError):
            logger.warning(f"Skipping file with invalid date format: {filepath.name}")
            continue

    if removed_count > 0:
        logger.info(f"Removed {removed_count} old articles")
    else:
        logger.info("No old articles to remove")


def generate_content_from_articles(articles):
    """
    Generate Hugo content files from a list of articles

    Args:
        articles: List of article dicts

    Returns:
        List of generated file paths
    """
    logger.info(f"Generating Hugo content for {len(articles)} articles...")

    # Ensure content directory exists
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    # Track existing files to avoid duplicates
    existing_files = set(f.name for f in CONTENT_DIR.glob('*.md'))

    generated_files = []
    skipped_count = 0

    for article in articles:
        filename = generate_article_filename(article)

        # Skip if file already exists
        if filename in existing_files:
            logger.debug(f"Skipping existing article: {filename}")
            skipped_count += 1
            continue

        try:
            filepath = write_article_file(article, filename)
            generated_files.append(filepath)
        except Exception as e:
            logger.error(f"Error writing article {filename}: {e}")
            continue

    logger.info(f"Generated {len(generated_files)} new articles")
    if skipped_count > 0:
        logger.info(f"Skipped {skipped_count} existing articles")

    return generated_files


def main():
    """
    Main function for standalone execution
    """
    try:
        # This would normally be called from run_daily.py with articles
        # For testing, we'll just clean up old articles
        logger.info("Running content generation cleanup...")
        cleanup_old_articles()

        logger.info("Content generation script ready")
        logger.info(f"Content directory: {CONTENT_DIR}")

    except Exception as e:
        logger.error(f"Error in content generation: {e}")
        raise


if __name__ == "__main__":
    main()
