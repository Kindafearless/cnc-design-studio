#!/bin/bash
# Quick activation script for CNC project
# Usage: source activate.sh

if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✓ CNC project environment activated"
    echo "  Python: $(python --version)"
    echo "  build123d installed: $(python -c 'import build123d; print(build123d.__version__)' 2>/dev/null || echo 'not found')"
    echo ""
    echo "Run: python parts/hamper.py to test the setup"
else
    echo "Error: .venv not found. Run setup first."
    exit 1
fi
