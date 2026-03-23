from setuptools import setup, find_packages

setup(
    name="price-monitor",
    version="1.0.0",
    description="Monitor product prices from e-commerce sites and get notifications",
    author="manggaladev",
    author_email="manggaladev@users.noreply.github.com",
    url="https://github.com/manggaladev/price-monitor-py",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=5.0.0",
        "sqlalchemy>=2.0.0",
        "apscheduler>=3.10.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "telegram": ["python-telegram-bot>=21.0"],
        "selenium": ["selenium>=4.18.0", "webdriver-manager>=4.0.0"],
        "api": ["fastapi>=0.110.0", "uvicorn>=0.27.0"],
        "dev": ["pytest>=8.0.0", "pytest-asyncio>=0.23.0"],
    },
    entry_points={
        "console_scripts": [
            "price-monitor=price_monitor.cli:main",
        ],
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
