#!/bin/bash

echo "Starting Project-to-Review (P2R)..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python is not installed or not in PATH."
    echo "Please install Python 3.7 or higher and try again."
    echo
    exit 1
fi

# Check if requirements are installed
echo "Checking dependencies..."
pip install -r requirements.txt

# Start the application
echo
echo "Starting P2R server..."
echo "Access the application at http://localhost:5000"
echo "Press Ctrl+C to stop the server."
echo
python3 main.py 