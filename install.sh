#!/bin/bash

# Exit on error
set -e

echo "=== AIVA 2026: Solder Defect Detector Setup ==="

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 could not be found. Please install Python 3."
    return 1 2>/dev/null || exit 1
fi

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment in '.venv'..."
    python3 -m venv .venv
else
    echo "Virtual environment '.venv' already exists."
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
if [ -f "requirements_dev.txt" ]; then
    pip install -r requirements_dev.txt
else
    echo "Error: requirements_dev.txt not found!"
    return 1 2>/dev/null || exit 1
fi

echo ""
echo "=== Setup Complete ==="
echo "El entorno ya está activado y listo para usarse."
