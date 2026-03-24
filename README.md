<div align="center">

# 🛒 Price Monitor

**Track product prices from e-commerce sites and get alerts when prices drop!**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D53230?style=for-the-badge)](https://sqlalchemy.org)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://telegram.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🛒 **Multi-site** | Tokopedia, Amazon, Shopee, Lazada |
| 💰 **Price Tracking** | Track price changes over time |
| 🔔 **Notifications** | Telegram & Email alerts |
| 📊 **Price History** | Charts & analytics |
| ⏰ **Scheduler** | Automatic periodic checks |
| 🖥️ **CLI** | Easy command-line interface |

## 🚀 Quick Start

```bash
# Clone
cd price-monitor-py

# Install
pip install -r requirements.txt

# Add product
python -m price_monitor add \
  --url "https://www.tokopedia.com/product/..." \
  --target 100000

# Start monitoring
python -m price_monitor scheduler
```

## 📸 Example Output

```
╔══════════════════════════════════════════════════════════════╗
║                    🛒 Price Monitor                           ║
╠══════════════════════════════════════════════════════════════╣
║  Product: iPhone 15 Pro Max                                  ║
║  Site:    Tokopedia                                          ║
║  Current: Rp 18.999.000                                      ║
║  Target:  Rp 17.000.000                                      ║
║  Status:  ⬆️ Above target by Rp 1.999.000                    ║
╚══════════════════════════════════════════════════════════════╝

🔔 Price Alert!
┌─────────────────────────────────────────────────────────────┐
│  iPhone 15 Pro Max dropped to Rp 16.999.000!                │
│  You save Rp 1.001.000 from your target!                    │
│  Buy now: https://tokopedia.com/...                         │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Commands

### Add Product
```bash
python -m price_monitor add \
  --url "https://www.amazon.com/dp/..." \
  --target 500 \
  --notes "Birthday gift"
```

### List Products
```bash
python -m price_monitor list
```

### Check Prices
```bash
# Check all
python -m price_monitor check

# Check specific
python -m price_monitor check --id 1
```

### Start Scheduler
```bash
# Default: check every 6 hours
python -m price_monitor scheduler

# Custom interval
python -m price_monitor scheduler --interval 60  # minutes
```

## 🔔 Notifications

### Telegram Setup

1. Create bot via [@BotFather](https://t.me/botfather)
2. Get your chat ID from [@userinfobot](https://t.me/userinfobot)
3. Configure:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Email Setup

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## 🏗️ Structure

```
price-monitor-py/
├── price_monitor/
│   ├── main.py           # Entry point
│   ├── config.py         # Configuration
│   ├── database/
│   │   ├── models.py     # SQLAlchemy models
│   │   └── crud.py       # Database operations
│   ├── scraper/
│   │   ├── base.py       # Base scraper
│   │   ├── tokopedia.py  # Tokopedia scraper
│   │   └── amazon.py     # Amazon scraper
│   ├── notifier/
│   │   ├── telegram.py   # Telegram bot
│   │   └── email.py      # Email sender
│   └── scheduler.py      # APScheduler setup
├── requirements.txt
└── setup.py
```

## 🛒 Supported Sites

| Site | Status | Notes |
|------|--------|-------|
| Tokopedia | ✅ | Full support |
| Amazon | ✅ | Multiple regions |
| Shopee | ✅ | SEA region |
| Lazada | ✅ | SEA region |
| Bukalapak | ✅ | Indonesia |

## ⚙️ Configuration

```env
# Database
DATABASE_URL=sqlite:///price_monitor.db

# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Email
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=

# Scraper
REQUEST_DELAY=1
MAX_RETRIES=3
```

## 📊 Database

SQLite by default, PostgreSQL for production:

```env
DATABASE_URL=postgresql://user:pass@localhost/price_monitor
```

## 🔧 API Integration

```python
from price_monitor.database import get_session
from price_monitor.database.crud import create_product

# Add product programmatically
with get_session() as db:
    product = create_product(db, {
        "url": "https://...",
        "target_price": 100000
    })
```

## 🤝 Contributing

Contributions welcome! Add more sites, improve scrapers.

## 📄 License

[MIT License](LICENSE)

---

<div align="center">

**[⬆ Back to Top](#-price-monitor)**


**Never miss a price drop again! 💰**

</div>
