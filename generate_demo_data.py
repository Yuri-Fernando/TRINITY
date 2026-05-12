"""
Generate demo data for dashboard without needing OpenAI API.
Run this to populate data/processed/ with sample index and scores.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

print("Generating demo data for Regulatory Uncertainty LLM Index...")

# Create directories
os.makedirs('data/processed', exist_ok=True)
os.makedirs('data/embeddings', exist_ok=True)

# Generate sample data
np.random.seed(42)
dates = pd.date_range(start='2026-03-15', end='2026-05-11', freq='D')

# Create realistic uncertainty pattern
scores = []
for i, date in enumerate(dates):
    # Trend: increasing uncertainty over time
    trend = 0.35 + 0.15 * (i / len(dates))

    # Seasonal: 30-day cycle
    seasonal = 0.08 * np.sin(2 * np.pi * i / 30)

    # Noise
    noise = np.random.normal(0, 0.05)

    base_score = np.clip(trend + seasonal + noise, 0, 1)

    # Generate 3-5 documents per day
    n_docs = np.random.randint(3, 6)
    for j in range(n_docs):
        doc_variation = np.random.normal(0, 0.08)
        score = np.clip(base_score + doc_variation, 0, 1)

        # Map score to level
        if score < 0.33:
            level = 'LOW'
        elif score < 0.67:
            level = 'MODERATE'
        else:
            level = 'HIGH'

        scores.append({
            'chunk_id': f'demo_{i:03d}_{j:02d}',
            'timestamp': date,
            'score': score,
            'confidence': np.random.uniform(0.75, 0.99),
            'uncertainty_level': level,
            'regulatory_domain': np.random.choice(['credit', 'market', 'operational']),
            'signals': ['ambiguous_language'] if score > 0.4 else [],
            'keywords': ['may', 'pending'] if score > 0.5 else []
        })

df_scores = pd.DataFrame(scores)

# Generate daily index
daily_index = []
for date in dates:
    day_data = df_scores[df_scores['timestamp'].dt.date == date.date()]

    if len(day_data) > 0:
        index_val = (day_data['score'] * day_data['confidence']).mean()
        volatility = day_data['score'].std()

        # EMA
        if len(daily_index) > 0:
            prev_ema = daily_index[-1]['smoothed_index']
            smoothed = 0.3 * index_val + 0.7 * prev_ema
        else:
            smoothed = index_val

        daily_index.append({
            'date': date,
            'index_value': index_val,
            'volatility': volatility,
            'smoothed_index': smoothed,
            'signal_count': len(day_data[day_data['uncertainty_level'].isin(['HIGH', 'CRITICAL'])]),
            'document_count': len(day_data)
        })

df_index = pd.DataFrame(daily_index)

# Export
df_index.to_csv('data/processed/index_pipeline.csv', index=False)
df_scores.to_csv('data/processed/scores_pipeline.csv', index=False)

print(f"[OK] Generated {len(df_scores)} score records")
print(f"[OK] Generated {len(df_index)} daily index values")
print(f"[OK] Saved to data/processed/")
print()
print("Statistics:")
print(f"  Index mean: {df_index['index_value'].mean():.4f}")
print(f"  Index std: {df_index['index_value'].std():.4f}")
print(f"  Score mean: {df_scores['score'].mean():.4f}")
print(f"  Domains: {df_scores['regulatory_domain'].unique()}")
print()
print("Now run: streamlit run dashboard/app.py")
