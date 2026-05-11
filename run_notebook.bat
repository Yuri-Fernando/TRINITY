@echo off
REM Quick script to run Jupyter notebook with full pipeline

echo Starting Regulatory Uncertainty Index Notebook...

REM Check venv
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate
call venv\Scripts\activate.bat

REM Install deps
python -c "import jupyter" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -q -r requirements.txt
)

REM Create dirs
if not exist "data\raw" mkdir data\raw
if not exist "data\processed" mkdir data\processed
if not exist "data\embeddings" mkdir data\embeddings
if not exist "logs" mkdir logs

REM Check .env
if not exist ".env" (
    echo Warning: .env not found. Creating from .env.example...
    copy .env.example .env
    echo Edit .env and add your OPENAI_API_KEY
)

REM Run notebook
jupyter notebook notebooks/exploratory_analysis.ipynb
