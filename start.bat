@echo off
echo ======================================
echo Smart City Parking - Web Application
echo ======================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Check if .env exists
if not exist ".env" (
    echo Creating .env file...
    (
        echo MONGO_URI=mongodb://localhost:27017/smartcity_parking
        echo JWT_SECRET_KEY=super-secret-jwt-key-change-in-production
        echo SECRET_KEY=super-secret-flask-key-change-in-production
        echo UPLOAD_FOLDER=static/uploads
    ) > .env
    echo .env file created with default values
)

echo.
echo ======================================
echo Starting application...
echo ======================================
echo.
echo Access the application at:
echo   - Home: http://localhost:5000
echo   - Login: http://localhost:5000/login
echo   - Register: http://localhost:5000/register
echo   - Admin: http://localhost:5000/secret-admin-panel
echo.
echo Admin Credentials:
echo   - Username: admin
echo   - Password: Smartparking123
echo.
echo ======================================
echo.

REM Start the application
python app.py

pause
