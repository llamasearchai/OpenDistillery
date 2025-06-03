#!/usr/bin/env python3
"""
OpenDistillery: Advanced Compound AI Systems for Enterprise Workflow Transformation
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="opendistillery",
    version="2.0.2",
    author="Nik Jois",
    author_email="nikjois@llamasearch.ai",
    description="Advanced Compound AI Systems for Enterprise Workflow Transformation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/opendistillery/opendistillery",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "isort>=5.12.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ],
        "enterprise": [
            "kubernetes>=28.1.0",
            "docker>=6.1.3",
            "boto3>=1.34.0",
            "azure-storage-blob>=12.19.0",
            "google-cloud-storage>=2.10.0",
        ],
        "research": [
            "jupyter>=1.0.0",
            "ipykernel>=6.26.0",
            "matplotlib>=3.8.2",
            "seaborn>=0.13.0",
            "plotly>=5.17.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "opendistillery=opendistillery.cli:main",
            "opendistillery-server=opendistillery.api.server:main",
            "opendistillery-worker=opendistillery.workers.celery_worker:main",
        ],
    },
    include_package_data=True,
    package_data={
        "opendistillery": [
            "config/*.yaml",
            "templates/*.json",
            "schemas/*.json",
        ],
        "": [
            "OpenDistillery.png",
            "OpenDistillery.svg",
            "*.md",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/opendistillery/opendistillery/issues",
        "Source": "https://github.com/opendistillery/opendistillery",
        "Documentation": "https://docs.opendistillery.ai",
    },
) 