# 🛒📉 Price Monitor Python

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)](https://github.com/manggaladev/price-monitor-py)

A Python application for monitoring product prices from e-commerce sites and sending notifications when prices drop below your target.

## ✨ Features

- 🔍 **Multi-site Support** - Monitor products from Tokopedia, Amazon, Shopee, Lazada, Bukalapak
- 💰 **Price Tracking** - Automatic price checks at configurable intervals
- 📊 **Price History** - Track price changes over time
- 🔔 **Notifications** - Telegram and email alerts when price drops below target
- 🖥️ **CLI Interface** - Easy-to-use command line tool
- ⏰ **Scheduler** - APScheduler for automatic periodic checks
- 🗃️ **Database** - SQLite (dev) or PostgreSQL (production)

## 🛠️ Tech Stack

- **Python 3.10+**
- **SQLAlchemy** - ORM
- **Alembic** - Migrations
- **APScheduler** - Job scheduling
- **BeautifulSoup4** - Web scraping
- **python-telegram-bot** - Telegram notifications
- **Click + Rich** - CLI

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/manggaladev/price-monitor-py.git
cd price-monitor-py

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

## 🚀 Usage

### Add Product to Monitor

```bash
python -m price_monitor add --url "https://www.tokopedia.com/product/..." --target 100000
```

### List Monitored Products

```bash
python -m price_monitor list
```

### Check Prices

```bash
# Check all products
python -m price_monitor check

# Check specific product
python -m price_monitor check --id 1
```

### Start Scheduler

```bash
# Run scheduler (continuous monitoring)
python -m price_monitor scheduler --interval 60  # every 60 minutes
```

### Telegram Bot

```bash
# Start telegram bot for notifications
python -m price_monitor bot
```

## 📁 Project Structure

```
price-monitor-py/
├── price_monitor/
│   ├── __init__.py
│   ├── cli.py           # CLI commands
│   ├── models/          # SQLAlchemy models
│   ├── scrapers/        # Site-specific scrapers
│   ├── notifiers/       # Notification services
│   └── scheduler.py     # APScheduler setup
├── tests/
├── scripts/
├── requirements.txt
├── setup.py
└── README.md
```

## 📄 License

[MIT License](LICENSE)

## 🔗 Links

- [GitHub Repository](https://github.com/manggaladev/price-monitor-py)
- [Issues](https://github.com/manggaladev/price-monitor-py/issues)
