@echo off
REM Run Jupyter Notebook for Exploratory Analysis
REM Usage: run_notebook.bat

setlocal enabledelayedexpansion

echo ==========================================
echo Regulatory Uncertainty LLM Index
echo Exploratory Analysis Notebook
echo ==========================================
echo.

REM Check if venv exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if requirements installed
python -c "import jupyter" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -q -r requirements.txt
)

REM Create data directories
if not exist "data\raw" mkdir data\raw
if not exist "data\processed" mkdir data\processed
if not exist "data\embeddings" mkdir data\embeddings
if not exist "logs" mkdir logs

REM Check .env file
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Creating .env from .env.example...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit .env and add your OPENAI_API_KEY
    echo Edit the file: .env
    echo.
    set /p continue="Have you updated .env with your API key? (y/n) "
    if /i not "!continue!"=="y" (
        echo Please edit .env first, then run this script again.
        exit /b 1
    )
)

REM Load environment variables from .env
for /f "usebackq delims==" %%A in (.env) do (
    if not "%%A"=="" (
        if not "%%A:~0,1%"=="#" (
            set %%A
        )
    )
)

REM Verify API key is set
if "!OPENAI_API_KEY!"=="" (
    echo ERROR: OPENAI_API_KEY not set in .env
    exit /b 1
)
if "!OPENAI_API_KEY!"=="sk-your-api-key-here" (
    echo ERROR: OPENAI_API_KEY still has placeholder value in .env
    exit /b 1
)

echo.
echo Starting Jupyter Notebook...
echo Opening: http://localhost:8888
echo.
echo Notebook: notebooks/exploratory_analysis.ipynb
echo.
echo Press Ctrl+C to stop the server
echo.

jupyter notebook notebooks/exploratory_analysis.ipynb

pause
