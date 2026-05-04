#!/usr/bin/env bash
set -e

echo "=== AIVA 2026: Solder Defect Detector Setup ==="

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 could not be found. Please install Python 3."
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment in '.venv'..."
    python3 -m venv .venv
else
    echo "Virtual environment '.venv' already exists."
fi

echo "Activating virtual environment..."
# shellcheck disable=SC1091
source .venv/bin/activate

echo "Using Python: $(which python)"

echo "Upgrading pip..."
python -m pip install --upgrade pip --no-cache-dir

echo "Cleaning pip cache..."
rm -rf ~/.cache/pip || true

echo "Installing Torch CPU for Raspberry Pi..."
python -m pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

echo "Installing lightweight project dependencies..."
python -m pip install --no-cache-dir numpy opencv-python pillow matplotlib psutil scipy pyyaml requests polars ultralytics-thop

echo "Installing Ultralytics without auto-dependencies..."
python -m pip install --no-cache-dir ultralytics --no-deps

echo ""
echo "Listing XML files in project:"
find . -type f \( -iname "*.xml" -o -iname "*.XML" \) -print || true

echo ""
echo "=== Setup Complete ==="
echo "El entorno ya está activado y listo para usarse."