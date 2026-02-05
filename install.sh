#!/bin/bash

echo "========================================"
echo "  Parking Management System Installer"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 is installed: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Installing pip..."
    sudo apt-get update
    sudo apt-get install -y python3-pip
fi

echo "✓ pip3 is installed"

# Install MongoDB if not installed
if ! command -v mongod &> /dev/null; then
    echo "📦 MongoDB is not installed. Installing MongoDB..."
    sudo apt-get update
    sudo apt-get install -y mongodb
    sudo systemctl start mongodb
    sudo systemctl enable mongodb
    echo "✓ MongoDB installed and started"
else
    echo "✓ MongoDB is already installed"
    
    # Make sure MongoDB is running
    if ! sudo systemctl is-active --quiet mongodb; then
        echo "Starting MongoDB..."
        sudo systemctl start mongodb
    fi
fi

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip3 install --break-system-packages -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Python dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Run database setup
echo ""
echo "🔧 Setting up database..."
python3 setup.py

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "  ✅ Installation Complete!"
    echo "========================================"
    echo ""
    echo "To start the application, run:"
    echo "  python3 app.py"
    echo ""
    echo "Then visit: http://localhost:5000"
    echo ""
    echo "Test User Login:"
    echo "  Email: test@parking.com"
    echo "  Password: test123"
    echo ""
else
    echo "❌ Database setup failed. Please check MongoDB connection."
    exit 1
fi
