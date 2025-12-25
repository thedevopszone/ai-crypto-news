"""
AI-powered article rewriting and translation using OpenAI
"""

from openai import OpenAI
import time

from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_MAX_TOKENS
from utils import setup_logger

logger = setup_logger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


def build_rewrite_prompt(title, content, coins):
    """
    Build prompt for OpenAI to rewrite article in German

    Args:
        title: Original article title
        content: Original article content
        coins: List of relevant coins

    Returns:
        System and user prompts
    """
    # Extract coin names
    coin_names = [coin['name'] for coin in coins] if coins else []
    coins_str = ", ".join(coin_names) if coin_names else "Kryptowährungen"

    system_prompt = """Du bist ein professioneller Krypto-Journalist, der Nachrichten
auf Deutsch schreibt. Deine Aufgabe ist es, englische Krypto-News-Artikel komplett
neu zu formulieren und auf Deutsch zu veröffentlichen.

Wichtig:
- Behalte alle Fakten, Zahlen und wichtigen Informationen bei
- Schreibe den Artikel komplett neu in deinen eigenen Worten
- Verwende einen professionellen, informativen Stil
- Schreibe 500-800 Wörter
- Nutze klare, präzise Sprache
- Erstelle einen ansprechenden deutschen Titel"""

    user_prompt = f"""Schreibe den folgenden Krypto-News-Artikel komplett neu auf Deutsch.

Relevante Kryptowährungen: {coins_str}

Original-Titel: {title}

Original-Inhalt:
{content[:4000]}

Bitte erstelle:
1. Einen ansprechenden deutschen Titel
2. Eine kurze Zusammenfassung (2-3 Sätze)
3. Den vollständigen Artikel auf Deutsch (500-800 Wörter)

Format deine Antwort als JSON:
{{
  "title": "Deutscher Titel hier",
  "summary": "Kurze Zusammenfassung hier",
  "content": "Vollständiger deutscher Artikel hier"
}}"""

    return system_prompt, user_prompt


def rewrite_article_german(title, content, coins):
    """
    Rewrite article in German using OpenAI

    Args:
        title: Original title
        content: Original content
        coins: List of relevant coin dicts

    Returns:
        Dict with 'title', 'summary', 'content' in German or None if failed
    """
    try:
        logger.info(f"Rewriting article with OpenAI: {title[:50]}...")

        # Build prompts
        system_prompt, user_prompt = build_rewrite_prompt(title, content, coins)

        # Call OpenAI API
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=OPENAI_MAX_TOKENS,
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        # Extract response
        result_text = response.choices[0].message.content

        # Parse JSON response
        import json
        result = json.loads(result_text)

        # Log token usage for cost tracking
        tokens_used = response.usage.total_tokens
        logger.info(f"Article rewritten. Tokens used: {tokens_used}")

        # Validate result
        if 'title' in result and 'content' in result:
            # Ensure we have a summary
            if 'summary' not in result or not result['summary']:
                # Create summary from first 2 sentences
                sentences = result['content'].split('.')[:2]
                result['summary'] = '.'.join(sentences) + '.'

            return result
        else:
            logger.error(f"Invalid response format from OpenAI: {result_text[:200]}")
            return None

    except Exception as e:
        logger.error(f"OpenAI rewriting failed: {e}")
        return retry_with_backoff(title, content, coins)


def retry_with_backoff(title, content, coins, max_retries=3):
    """
    Retry OpenAI request with exponential backoff

    Args:
        title: Article title
        content: Article content
        coins: Relevant coins
        max_retries: Maximum number of retries

    Returns:
        Rewritten article or None
    """
    for attempt in range(max_retries):
        try:
            delay = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
            logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {delay}s delay")
            time.sleep(delay)

            system_prompt, user_prompt = build_rewrite_prompt(title, content, coins)

            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=OPENAI_MAX_TOKENS,
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)

            if 'title' in result and 'content' in result:
                if 'summary' not in result:
                    sentences = result['content'].split('.')[:2]
                    result['summary'] = '.'.join(sentences) + '.'
                return result

        except Exception as e:
            logger.warning(f"Retry {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                logger.error("All retries exhausted")
                return None

    return None


def main():
    """
    Test AI rewriter functionality
    """
    logger.info("Testing AI rewriter...")

    test_title = "Bitcoin Surges as Institutional Investors Show Renewed Interest"
    test_content = """Bitcoin continues its upward trajectory as institutional investors
show renewed interest in the cryptocurrency market. The leading digital asset climbed
above $95,000 this week, marking a significant milestone. Analysts attribute this
surge to increased adoption by major financial institutions and growing confidence
in crypto as a hedge against inflation. MicroStrategy and other corporate giants
continue to add Bitcoin to their balance sheets, signaling strong long-term conviction."""

    test_coins = [
        {'symbol': 'btc', 'name': 'Bitcoin'},
        {'symbol': 'eth', 'name': 'Ethereum'}
    ]

    result = rewrite_article_german(test_title, test_content, test_coins)

    if result:
        logger.info(f"\nGerman Title: {result['title']}")
        logger.info(f"\nSummary: {result['summary']}")
        logger.info(f"\nContent ({len(result['content'])} chars):\n{result['content'][:300]}...")
    else:
        logger.error("Rewriting failed")


if __name__ == "__main__":
    main()
