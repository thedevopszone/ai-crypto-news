# Crypto News Daily

A Hugo-based static website that displays the latest cryptocurrency news for Bitcoin and top 99 altcoins, automatically fetched daily from Google News using the GNews API.

## Features

- **Daily Updates**: Automatically fetches news once per day via GitHub Actions
- **100 Cryptocurrencies**: Covers Bitcoin + top 99 altcoins by market cap
- **Comprehensive News Display**: Shows headlines, summaries, thumbnails, sources, and publication dates
- **Responsive Design**: Mobile-first design that works on all devices
- **Zero Maintenance**: Fully automated with GitHub Actions and GitHub Pages
- **Free Hosting**: Deployed on GitHub Pages

## Architecture

### Components

1. **Data Fetching Layer** (Python)
   - Fetches top 100 cryptocurrencies from CoinGecko API
   - Fetches news from GNews API using aggregated search
   - Matches articles to specific coins via keyword matching

2. **Content Generation Layer** (Python → Hugo)
   - Converts news articles into Hugo markdown files
   - Handles deduplication and cleanup of old articles

3. **Static Site Layer** (Hugo)
   - Generates static website from markdown files
   - Custom responsive theme

4. **Automation Layer** (GitHub Actions)
   - Runs daily at 2 AM UTC
   - Fetches data, builds site, deploys to GitHub Pages

## Setup Instructions

### Prerequisites

- GitHub account
- GNews API key (free tier: 100 requests/day)
- Python 3.10+ (for local testing)
- Hugo (for local testing)

### 1. Get API Keys

#### GNews API (Required)
1. Visit [gnews.io](https://gnews.io/)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Free tier: 100 requests/day (sufficient for this project)

#### CoinGecko API (Optional)
1. Visit [coingecko.com](https://www.coingecko.com/en/api)
2. Free tier works without an API key
3. Optional: Get API key for higher rate limits

### 2. Fork/Clone Repository

```bash
git clone https://github.com/yourusername/ai-crypto-news.git
cd ai-crypto-news
```

### 3. Configure GitHub Secrets

Add these secrets to your GitHub repository:

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Add the following secrets:

- `GNEWS_API_KEY`: Your GNews API key (required)
- `COINGECKO_API_KEY`: Your CoinGecko API key (optional)

### 4. Update Configuration

Edit `site/config.toml`:

```toml
baseURL = "https://yourusername.github.io/ai-crypto-news/"
```

Replace `yourusername` with your GitHub username.

### 5. Enable GitHub Pages

1. Go to **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: **gh-pages** / **(root)**
4. Click **Save**

### 6. Run Workflow

The workflow runs automatically:
- **Daily at 2 AM UTC** (scheduled)
- **On push to main branch** (optional)
- **Manually** via Actions tab

To trigger manually:
1. Go to **Actions** tab
2. Click **Daily Crypto News Update**
3. Click **Run workflow**

## Local Development

### Setup Local Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env and add your GNEWS_API_KEY
```

### Test Scripts

```bash
# Test fetching coins
cd scripts
python3 fetch_coins.py

# Test fetching news
python3 fetch_news.py

# Test content generation
python3 generate_content.py

# Run full pipeline
python3 run_daily.py
```

### Preview Site Locally

```bash
# Install Hugo (if not already installed)
# macOS: brew install hugo
# Ubuntu: sudo apt-get install hugo
# Windows: choco install hugo-extended

# Build and serve site
cd site
hugo server -D

# Visit http://localhost:1313
```

## Project Structure

```
ai-crypto-news/
├── .github/
│   └── workflows/
│       └── daily-update.yml       # GitHub Actions workflow
├── scripts/
│   ├── config.py                  # Configuration management
│   ├── utils.py                   # Utility functions
│   ├── fetch_coins.py             # Fetch top 100 coins
│   ├── fetch_news.py              # Fetch news from GNews
│   ├── generate_content.py        # Generate Hugo markdown
│   └── run_daily.py               # Main orchestrator
├── site/
│   ├── config.toml                # Hugo configuration
│   ├── content/news/              # Generated news articles
│   ├── layouts/                   # Hugo templates
│   ├── static/                    # CSS, images, JS
│   └── public/                    # Generated site (gitignored)
├── data/
│   └── coins.json                 # Cached top 100 coins
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
├── .gitignore
└── README.md
```

## How It Works

### API Rate Limit Strategy

The GNews API free tier allows 100 requests/day, but we need to cover 100 cryptocurrencies. The solution:

1. **Aggregated Search**: Instead of 100 separate queries, we use 1-2 queries with OR logic:
   ```
   "cryptocurrency OR bitcoin OR ethereum OR cardano OR solana..."
   ```

2. **Keyword Matching**: After fetching up to 100 articles, we match them to specific coins by searching for coin names/symbols in titles and descriptions.

3. **Relevance Scoring**: Articles are ranked by how well they match each coin.

### Daily Workflow

1. **2:00 AM UTC**: GitHub Actions triggers
2. **Fetch Coins**: Get top 100 coins by market cap from CoinGecko
3. **Fetch News**: Get up to 100 articles from GNews using aggregated search
4. **Match Articles**: Associate articles with relevant coins
5. **Generate Content**: Create Hugo markdown files
6. **Build Site**: Hugo generates static site
7. **Deploy**: Push to gh-pages branch
8. **Commit**: Save updated data and content files

## Customization

### Change Update Time

Edit `.github/workflows/daily-update.yml`:

```yaml
on:
  schedule:
    - cron: '0 14 * * *'  # 2 PM UTC
```

### Adjust Number of Coins

Edit `.env` or GitHub Secrets:

```bash
TOP_N_COINS=50  # Track only top 50 coins
```

### Keep Articles Longer

```bash
DAYS_TO_KEEP=60  # Keep 60 days instead of 30
```

### Customize Styling

Edit `site/static/css/style.css` to change colors, fonts, layout, etc.

## Troubleshooting

### Workflow Fails

1. Check GitHub Actions logs for errors
2. Verify API keys are set correctly in Secrets
3. Ensure GNews API quota hasn't been exceeded

### No Articles Appearing

1. Check if workflow ran successfully
2. Verify news was fetched (check logs)
3. Ensure Hugo build completed without errors
4. Check if gh-pages branch was updated

### API Rate Limits

- **CoinGecko**: 10-30 calls/minute (free tier) - should never be an issue
- **GNews**: 100 requests/day - we use only 1-2 per run

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this project for your own crypto news site!

## Credits

- News data from [GNews API](https://gnews.io/)
- Cryptocurrency data from [CoinGecko API](https://www.coingecko.com/)
- Built with [Hugo](https://gohugo.io/)
- Deployed on [GitHub Pages](https://pages.github.com/)

## Support

If you encounter any issues, please [open an issue](https://github.com/yourusername/ai-crypto-news/issues) on GitHub.
