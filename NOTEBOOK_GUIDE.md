# Notebook Guide – Exploratory Analysis

## Quick Start

### Windows
```batch
run_notebook.bat
```

### Linux / macOS
```bash
chmod +x run_notebook.sh
./run_notebook.sh
```

---

## Manual Setup (Step by Step)

### 1. Create Virtual Environment

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Jupyter and Jupyter Notebook
- Pandas, NumPy, Matplotlib, Seaborn
- All project dependencies

### 3. Setup Environment Variables

**Copy the example file:**
```bash
cp .env.example .env
```

**Edit `.env` and add your OpenAI API key:**
```
OPENAI_API_KEY=sk-your-real-api-key-here
```

Get your key from: https://platform.openai.com/api-keys

### 4. Create Data Directories

```bash
mkdir -p data/raw data/processed data/embeddings logs
```

### 5. Start Jupyter Notebook

```bash
jupyter notebook
```

Then navigate to: `notebooks/exploratory_analysis.ipynb`

---

## What the Notebook Does

### Cell 1-2: Setup & Imports
- Configures environment and plotting
- Imports required libraries

### Cell 3: Load Sample Data
- Generates synthetic uncertainty scores for demo
- Creates 90 days of data with realistic patterns:
  - Trend component
  - Seasonal component (30-day cycle)
  - Random noise
  - Multiple documents per day

**Output:** DataFrame with 900 documents

### Cell 4: Distribution Analysis
- Histogram of uncertainty scores
- Bar chart of uncertainty levels
- Average scores by regulatory domain
- Confidence vs. Score scatter plot

### Cell 5: Temporal Analysis
- Daily index values over time
- Volatility bands (±1 std dev)
- Exponential Moving Average (EMA)
- Index statistics (mean, std, min, max)

### Cell 6: Domain-Specific Analysis
- Separate indices for: credit, market, operational
- Domain correlation matrix

### Cell 7: Top Uncertainty Events
- Top 10 high uncertainty documents
- Timeline of HIGH/CRITICAL events

### Cell 8: Validation Checks
- Autocorrelation (should be ~0.7-0.8)
- Missing value detection
- Data quality checks
- Documents per date statistics

### Cell 9: Export Results
- Exports daily index to `data/processed/index_exploratory.csv`
- Exports raw scores to `data/processed/scores_exploratory.csv`

---

## Running Individual Cells

Click on a cell and press:
- **Shift + Enter** – Run current cell
- **Ctrl + Enter** – Run current cell, stay in same cell
- **Alt + Enter** – Run current cell, create new cell below

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'jupyter'"
```bash
pip install jupyter notebook
```

### "OpenAI API Error: 401"
- Check your API key in `.env` is correct
- Verify key has no extra spaces: `sk-... ` (trailing space breaks it)
- Test: `echo $OPENAI_API_KEY` (Linux/Mac) or `echo %OPENAI_API_KEY%` (Windows)

### "No module named 'pandas'"
```bash
pip install -r requirements.txt
```

### Notebook won't open in browser
- Look for URL in terminal: `http://localhost:8888/?token=...`
- Copy and paste into browser
- Or access at `http://localhost:8888` and provide token when asked

### Cell 3 fails (No module named 'numpy')
```bash
pip install numpy pandas scipy scikit-learn matplotlib seaborn
```

### Slow performance on Cell 3 (generating data)
- This is normal for the first run (~10-30 seconds)
- Subsequent cell runs will be faster

---

## Customizing the Notebook

### Change Sample Data Seed
In Cell 3, modify:
```python
np.random.seed(42)  # Change to different number
```

### Change Date Range
```python
dates = pd.date_range(start='2026-01-01', end='2026-05-11', freq='D')
```

### Add More Documents Per Day
```python
for j in range(3):  # Change 3 to higher number
```

### Adjust Trend / Seasonality
```python
trend = 0.4 + 0.1 * (i / len(dates))  # Modify coefficients
seasonal = 0.1 * np.sin(2 * np.pi * i / 30)  # Modify amplitude/period
```

---

## Exporting Results

The notebook automatically exports to:
- `data/processed/index_exploratory.csv` – Daily index values
- `data/processed/scores_exploratory.csv` – Raw classification scores

Import results in other tools:
```python
import pandas as pd

index_df = pd.read_csv('data/processed/index_exploratory.csv')
scores_df = pd.read_csv('data/processed/scores_exploratory.csv')
```

---

## Next Steps

1. **Modify sample data generation** to reflect your real data pattern
2. **Connect to real data source** in Cell 3 (replace with actual ingestion)
3. **Run classification pipeline** on real documents
4. **Validate against economic indicators** (VIX, credit spreads, etc.)
5. **Deploy to production** with real Fed/SEC data

---

## Performance Notes

| Operation | Time |
|-----------|------|
| Data generation (Cell 3) | ~10-30s |
| Distribution plots (Cell 4) | ~2-5s |
| Temporal analysis (Cell 5) | ~3-8s |
| Domain analysis (Cell 6) | ~2-4s |
| Export (Cell 9) | <1s |
| **Total first run** | **~20-50s** |

Memory usage: ~100-200 MB (minimal)

---

## Security Notes

- **Never commit `.env` with real API keys**
- `.env` is in `.gitignore` – it won't be tracked
- Use `.env.example` as template for sharing
- Rotate API keys if accidentally exposed
- Use environment variables in production, not `.env` files

---

## Getting Help

If you encounter issues:

1. **Check the error message** in the notebook output
2. **Run from terminal** instead of IDE:
   ```bash
   jupyter notebook
   ```
3. **Verify dependencies:**
   ```bash
   pip list | grep -E "jupyter|pandas|numpy|matplotlib"
   ```
4. **Clear notebook cache:**
   ```bash
   find . -type d -name __pycache__ -exec rm -r {} +
   find . -type d -name .ipynb_checkpoints -exec rm -r {} +
   ```

---

**Happy analyzing!**
