#!/bin/bash
# Build script for Linux
# Ensure we are in the project directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run PyInstaller
pyinstaller --noconfirm --onefile --windowed --name "PhotoOrganizer" --add-data "src:src" src/main.py
echo "Build complete. Executable is in dist/PhotoOrganizer"
