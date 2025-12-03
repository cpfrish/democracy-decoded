#!/bin/bash
# Quick Start Script - Congressional Data Analysis

echo "=========================================="
echo "Congressional Data Analysis - Quick Start"
echo "=========================================="
echo

# Check for API key
if [ -z "$CONGRESS_API_KEY" ]; then
    echo "ERROR: CONGRESS_API_KEY not set"
    echo
    echo "Get an API key at: https://api.congress.gov/sign-up/"
    echo "Then run: export CONGRESS_API_KEY='your_key_here'"
    exit 1
fi

echo "✓ API key found"
echo

# Check Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "ERROR: Python not found"
    exit 1
fi

PYTHON_CMD=$(command -v python3 || command -v python)
echo "✓ Python found: $PYTHON_CMD"
echo

# Check dependencies
echo "Checking dependencies..."
$PYTHON_CMD -c "import pandas, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    $PYTHON_CMD -m pip install -r requirements.txt
fi

echo "✓ Dependencies OK"
echo
echo "=========================================="
echo "Ready to run!"
echo "=========================================="
echo
echo "Choose an option:"
echo "  1. Run all steps (recommended, ~5 min)"
echo "  2. Run step 1 only (fetch members)"
echo "  3. Run step 2 only (fetch locations)"
echo "  4. Run step 3 only (create visualizations)"
echo "  5. Exit"
echo
read -p "Enter choice (1-5): " choice

case $choice in
    1)
        $PYTHON_CMD run_all.py
        ;;
    2)
        $PYTHON_CMD 1_fetch_member_data.py
        ;;
    3)
        $PYTHON_CMD 2_fetch_location_data.py
        ;;
    4)
        $PYTHON_CMD 3_create_visualizations.py
        ;;
    5)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo
echo "=========================================="
echo "✓ Complete!"
echo "=========================================="
echo
echo "View your visualizations:"
echo "  - visualizations/member_activity_scatter_interactive.html"
echo "  - visualizations/congress_map_dual_chamber.html"
echo
