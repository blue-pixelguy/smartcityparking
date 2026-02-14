#!/bin/bash

echo "======================================"
echo "Smart City Parking - Web Application"
echo "======================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
MONGO_URI=mongodb://localhost:27017/smartcity_parking
JWT_SECRET_KEY=super-secret-jwt-key-change-in-production
SECRET_KEY=super-secret-flask-key-change-in-production
UPLOAD_FOLDER=static/uploads
EOF
    echo ".env file created with default values"
fi

echo ""
echo "======================================"
echo "Starting application..."
echo "======================================"
echo ""
echo "Access the application at:"
echo "  - Home: http://localhost:5000"
echo "  - Login: http://localhost:5000/login"
echo "  - Register: http://localhost:5000/register"
echo "  - Admin: http://localhost:5000/secret-admin-panel"
echo ""
echo "Admin Credentials:"
echo "  - Username: admin"
echo "  - Password: Smartparking123"
echo ""
echo "======================================"
echo ""

# Start the application
python app.py
