# Price Monitor Python 🛒📉

A Python application for monitoring product prices from e-commerce sites and sending notifications when prices drop below your target.

## Features

- 🔍 **Multi-site Support**: Monitor products from Tokopedia, Amazon, Shopee, Lazada, Bukalapak
- 💰 **Price Tracking**: Automatic price checks at configurable intervals
- 📊 **Price History**: Track price changes over time
- 🔔 **Notifications**: Telegram and email alerts when price drops below target
- 🖥️ **CLI Interface**: Easy-to-use command line tool
- ⏰ **Scheduler**: APScheduler for automatic periodic checks
- 🗃️ **Database**: SQLite (dev) or PostgreSQL (production)

## Installation

### Prerequisites

- Python 3.10+
- pip or uv

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/manggaladev/price-monitor-py.git
   cd price-monitor-py
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Initialize database**
   ```bash
   python scripts/init_db.py
   # or
   price-monitor init-db
   ```

## Configuration

Edit `.env` file with your settings:

```env
# Database
DATABASE_URL=sqlite:///./price_monitor.db

# Telegram Bot (Required for notifications)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Email Notifications (Optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=recipient@example.com

# Scraping Settings
USER_AGENT=Mozilla/5.0 ...
REQUEST_DELAY=2
MAX_RETRIES=3

# Scheduler
DEFAULT_CHECK_INTERVAL=360  # minutes (6 hours)

# Logging
LOG_LEVEL=INFO
LOG_FILE=price_monitor.log
```

### Getting Telegram Credentials

1. Create a bot using [@BotFather](https://t.me/botfather):
   - Send `/newbot` and follow the instructions
   - Copy the **bot token**

2. Get your **Chat ID**:
   - Start a chat with your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Send a message to your bot
   - Refresh the URL and find `"chat":{"id":YOUR_CHAT_ID}`

## Usage

### CLI Commands

#### Add a product
```bash
# Basic usage
price-monitor add "https://tokopedia.com/product-url" --target 100000

# With options
price-monitor add "https://tokopedia.com/product-url" \
    --target 100000 \
    --interval 180 \
    --name "Product Name" \
    --notes "My notes"
```

#### List products
```bash
# List active products
price-monitor list

# Include paused products
price-monitor list --all
```

#### Check prices
```bash
# Check all products once
price-monitor run-once

# Check specific product
price-monitor check 1
```

#### Start scheduler
```bash
# Start monitoring (foreground)
price-monitor run
```

#### Update product
```bash
# Update target price
price-monitor update 1 --target 90000

# Pause monitoring
price-monitor update 1 --pause

# Resume monitoring
price-monitor update 1 --resume
```

#### View history
```bash
price-monitor history 1
```

#### Remove product
```bash
price-monitor remove 1
```

#### Test notifications
```bash
price-monitor test
```

### Programmatic Usage

```python
from price_monitor.database import ProductCRUD, init_db
from price_monitor.scraper import get_scraper
from price_monitor.notifier import send_price_alert

# Initialize database
init_db()

# Add a product
product = ProductCRUD.create(
    url="https://tokopedia.com/product/xyz",
    target_price=100000,
    name="My Product",
    check_interval=360,
)

# Get price manually
scraper = get_scraper(product.url)
result = scraper.get_price(product.url)
print(f"Price: {result.price}")

# Send notification
if result.price <= product.target_price:
    send_price_alert(
        product_name=product.name,
        current_price=result.price,
        target_price=product.target_price,
        url=product.url,
    )
```

## Adding New Scrapers

To add support for a new e-commerce site:

1. Create a new scraper file in `price_monitor/scraper/`:

```python
# price_monitor/scraper/newsite.py
from price_monitor.scraper.base import BaseScraper, ScraperResult

class NewSiteScraper(BaseScraper):
    SITE_NAME = "newsite"
    SUPPORTED_DOMAINS = ["newsite.com"]

    def get_price(self, url: str) -> ScraperResult:
        response = self._make_request(url)
        if not response:
            return ScraperResult(success=False, error="Failed to fetch")

        soup = self._parse_html(response)

        # Extract price from page
        price_element = soup.select_one(".price-selector")
        if price_element:
            price = parse_price(price_element.text)
            return ScraperResult(success=True, price=price)

        return ScraperResult(success=False, error="Price not found")
```

2. Register the scraper in `price_monitor/scraper/utils.py`:

```python
from price_monitor.scraper.newsite import NewSiteScraper

SCRAPER_REGISTRY = {
    "tokopedia": TokopediaScraper,
    "amazon": AmazonScraper,
    "newsite": NewSiteScraper,  # Add here
}
```

## Database Schema

### Product
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| url | String | Product URL |
| name | String | Product name |
| site | String | Site name |
| target_price | Float | Target price for alerts |
| current_price | Float | Last known price |
| check_interval | Integer | Check interval (minutes) |
| is_active | Boolean | Monitoring active |
| last_checked | DateTime | Last check time |
| created_at | DateTime | Creation time |

### PriceHistory
| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| product_id | Integer | Foreign key |
| price | Float | Recorded price |
| available | Boolean | Product available |
| checked_at | DateTime | Check time |

## Docker Support

```bash
# Build image
docker build -t price-monitor .

# Run container
docker run -d \
    --name price-monitor \
    -v $(pwd)/data:/app/data \
    -e TELEGRAM_BOT_TOKEN=your_token \
    -e TELEGRAM_CHAT_ID=your_chat_id \
    price-monitor
```

## Ethical Considerations

⚠️ **Important**: Web scraping should be done responsibly:

1. **Respect `robots.txt`**: Check if the site allows scraping
2. **Use reasonable delays**: Don't overwhelm servers
3. **Personal use only**: Don't redistribute scraped data
4. **Terms of Service**: Review and comply with site ToS
5. **Rate limiting**: This tool includes delays and retries to be respectful

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file.


**Happy price hunting!** 🎯💰
