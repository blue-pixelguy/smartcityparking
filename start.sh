#!/bin/bash

# Quick Start Script for P2P Parking System

echo "================================"
echo "P2P Parking - Quick Start"
echo "================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your actual values!"
    echo ""
fi

# Run diagnostic
echo "Running diagnostic check..."
python diagnose.py

if [ $? -eq 0 ]; then
    echo ""
    echo "================================"
    echo "Starting application..."
    echo "================================"
    python app.py
else
    echo ""
    echo "❌ Diagnostic failed! Please fix errors above."
    exit 1
fi