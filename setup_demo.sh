#!/bin/bash
# Quick setup script for Vanna Console Chat App Demo

set -e  # Exit on error

echo "========================================="
echo "Vanna Console Chat App - Quick Setup"
echo "========================================="
echo ""

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Warning: ANTHROPIC_API_KEY is not set"
    echo ""
    echo "Please set your API key:"
    echo "  export ANTHROPIC_API_KEY='your-key-here'"
    echo ""
    echo "Or create a .env file:"
    echo "  echo 'ANTHROPIC_API_KEY=your-key-here' > .env"
    echo ""
fi

# Check if Chinook database exists
if [ ! -f "Chinook.sqlite" ]; then
    echo "📥 Downloading Chinook demo database..."
    curl -o Chinook.sqlite https://vanna.ai/Chinook.sqlite
    echo "✅ Database downloaded!"
else
    echo "✅ Chinook.sqlite already exists"
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "To run the console chat app:"
echo "  python console_chat_app.py Chinook.sqlite"
echo ""
echo "Or make it executable and run:"
echo "  ./console_chat_app.py Chinook.sqlite"
echo ""
