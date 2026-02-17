#!/bin/bash
# Setup script for Supply Chain MVP Python environment

echo "Creating Python virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Virtual environment setup complete!"
echo "To activate the environment, run: source venv/bin/activate"
