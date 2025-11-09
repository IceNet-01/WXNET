#!/usr/bin/env python3
"""Setup script for WXNET."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = requirements_file.read_text().strip().split("\n")

setup(
    name="wxnet",
    version="1.0.0",
    description="Severe Weather Monitoring Terminal - Real-time storm tracking and analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="WXNET Development Team",
    author_email="dev@wxnet.example.com",
    url="https://github.com/your-repo/WXNET",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "wxnet=wxnet.app:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="weather storm-chasing radar severe-weather noaa nws terminal tui",
    python_requires=">=3.8",
    include_package_data=True,
    zip_safe=False,
)
