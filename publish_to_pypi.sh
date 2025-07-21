#!/bin/bash

# OpenDistillery PyPI Publishing Script
# Usage: ./publish_to_pypi.sh [your-pypi-token]

set -e

echo "🚀 OpenDistillery PyPI Publishing Script"
echo "========================================"

# Check if packages exist
if [ ! -d "dist" ] || [ -z "$(ls -A dist/)" ]; then
    echo "❌ No distribution packages found. Building packages..."
    python -m build
fi

# Verify packages
echo "📦 Verifying packages..."
python -m twine check dist/*

if [ $? -ne 0 ]; then
    echo "❌ Package verification failed!"
    exit 1
fi

echo "✅ Package verification passed!"

# Get token from parameter or environment
if [ -n "$1" ]; then
    PYPI_TOKEN="$1"
elif [ -n "$PYPI_API_TOKEN" ]; then
    PYPI_TOKEN="$PYPI_API_TOKEN"
else
    echo "❌ No PyPI token provided!"
    echo "Usage: ./publish_to_pypi.sh [your-pypi-token]"
    echo "Or set PYPI_API_TOKEN environment variable"
    exit 1
fi

echo "🔑 Using provided PyPI token..."

# Upload to PyPI
echo "📤 Uploading to PyPI..."
python -m twine upload dist/* \
    --username __token__ \
    --password "$PYPI_TOKEN" \
    --verbose

if [ $? -eq 0 ]; then
    echo "✅ Successfully published OpenDistillery v2.1.0 to PyPI!"
    echo "📦 Package available at: https://pypi.org/project/opendistillery/"
    echo "💾 Install with: pip install opendistillery"
else
    echo "❌ Failed to publish to PyPI"
    exit 1
fi 