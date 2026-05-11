#!/bin/bash

# Run Jupyter Notebook for Exploratory Analysis
# Usage: ./run_notebook.sh

set -e

echo "=========================================="
echo "Regulatory Uncertainty LLM Index"
echo "Exploratory Analysis Notebook"
echo "=========================================="
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Check if requirements installed
if ! python -c "import jupyter" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -q -r requirements.txt
fi

# Create data directories
mkdir -p data/raw data/processed data/embeddings
mkdir -p logs

# Check .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "WARNING: .env file not found!"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "IMPORTANT: Edit .env and add your OPENAI_API_KEY"
    echo "Edit the file: .env"
    echo ""
    read -p "Have you updated .env with your API key? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Please edit .env first, then run this script again."
        exit 1
    fi
fi

# Load environment
set -a
source .env
set +a

# Verify API key is set
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "sk-your-api-key-here" ]; then
    echo "ERROR: OPENAI_API_KEY not set correctly in .env"
    exit 1
fi

echo ""
echo "Starting Jupyter Notebook..."
echo "Opening: http://localhost:8888"
echo ""
echo "Notebook: notebooks/exploratory_analysis.ipynb"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

jupyter notebook notebooks/exploratory_analysis.ipynb
