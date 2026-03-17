"""
Price Monitor Python - E-commerce price monitoring tool.
"""

from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt", encoding="utf-8") as f:
    requirements = [
        line.strip()
        for line in f
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="price-monitor",
    version="1.0.0",
    author="manggaladev",
    author_email="manggaladev@users.noreply.github.com",
    description="E-commerce price monitoring and notification tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/manggaladev/price-monitor-py",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Office/Business :: Financial",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "price-monitor=price_monitor.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
