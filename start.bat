@echo off
echo Starting Project-to-Review (P2R)...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.7 or higher and try again.
    echo.
    pause
    exit /b 1
)

REM Check if requirements are installed
echo Checking dependencies...
pip install -r requirements.txt

REM Start the application
echo.
echo Starting P2R server...
echo Access the application at http://localhost:5000
echo Press Ctrl+C to stop the server.
echo.
python main.py 