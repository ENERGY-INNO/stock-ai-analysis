#!/bin/bash
# US Stock AI Analysis System Starter

echo "===================================================="
echo "   AI US Stock Analysis System - Starting Up       "
echo "===================================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found! Please check your GOOGLE_API_KEY."
fi

# Run the master python script
python3 run_all.py
