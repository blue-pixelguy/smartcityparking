#!/bin/bash
# Build script for Render deployment

set -e  # Exit on error

echo "================================"
echo "Starting Build Process"
echo "================================"

# Upgrade pip and install build tools first
echo "📦 Upgrading pip and installing build tools..."
pip install --upgrade pip setuptools wheel

# Install dependencies with verbose output
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt --no-cache-dir --verbose

# Verify critical imports
echo "✅ Verifying installations..."
python -c "import flask; print(f'Flask: {flask.__version__}')"
python -c "import bcrypt; print('bcrypt: OK')"
python -c "import pymongo; print('pymongo: OK')"
python -c "import jwt; print('PyJWT: OK')"
python -c "from PIL import Image; print('Pillow: OK')"

echo "================================"
echo "✅ Build Complete!"
echo "================================"