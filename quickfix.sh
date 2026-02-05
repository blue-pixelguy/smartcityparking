#!/bin/bash

# Quick Fix Script for Parking Management System
# This script fixes the deployment issues

echo "=========================================="
echo "  Parking System - Quick Fix Script"
echo "=========================================="
echo ""

cd parking || exit 1

echo "📋 Step 1: Backing up requirements.txt..."
cp requirements.txt requirements.txt.backup
echo "✓ Backup created"
echo ""

echo "📦 Step 2: Adding gunicorn to requirements.txt..."
if grep -q "gunicorn" requirements.txt; then
    echo "⚠️  gunicorn already exists in requirements.txt"
else
    echo "gunicorn==21.2.0" >> requirements.txt
    echo "✓ gunicorn added"
fi
echo ""

echo "🗑️  Step 3: Removing typo directories..."
if [ -d "statitc" ]; then
    rm -rf statitc
    echo "✓ Removed 'statitc' directory"
fi

if [ -d "{static" ]; then
    rm -rf "{static"
    echo "✓ Removed '{static' directory"
fi
echo ""

echo "🔍 Step 4: Verifying directory structure..."
echo ""
echo "Static directories found:"
ls -la | grep static || echo "No static directories found (ERROR!)"
echo ""

echo "📄 Step 5: Updated requirements.txt:"
cat requirements.txt
echo ""

echo "=========================================="
echo "✅ Fixes Applied Successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Review the changes"
echo "2. git add requirements.txt"
echo "3. git commit -m 'Fix: Add gunicorn and cleanup directories'"
echo "4. git push origin main"
echo "5. Redeploy on Render"
echo ""