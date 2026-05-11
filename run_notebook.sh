#!/bin/bash
# Quick script to run Jupyter notebook with full pipeline

echo "Starting Regulatory Uncertainty Index Notebook..."

# Check venv
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate
source venv/bin/activate

# Install deps
if ! python -c "import jupyter" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -q -r requirements.txt
fi

# Create dirs
mkdir -p data/raw data/processed data/embeddings logs

# Check .env
if [ ! -f ".env" ]; then
    echo "Warning: .env not found. Creating from .env.example..."
    cp .env.example .env
    echo "Edit .env and add your OPENAI_API_KEY"
fi

# Run notebook
jupyter notebook notebooks/exploratory_analysis.ipynb
