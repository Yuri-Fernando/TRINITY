"""
Regulatory Uncertainty LLM Index - Dashboard

Interactive Streamlit dashboard for monitoring regulatory uncertainty index.
"""

import sys
import os
sys.path.insert(0, '../src')

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# Configure page
st.set_page_config(
    page_title="Regulatory Uncertainty Index",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .high-uncertainty {
        color: #d32f2f;
        font-weight: bold;
    }
    .moderate-uncertainty {
        color: #f57c00;
        font-weight: bold;
    }
    .low-uncertainty {
        color: #388e3c;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("📊 Regulatory Uncertainty LLM Index Dashboard")
st.markdown("Real-time monitoring of regulatory uncertainty signals")

# Load data
@st.cache_data
def load_index_data():
    """Load index timeseries data."""
    # Try multiple paths
    paths = [
        'data/processed/index_pipeline.csv',
        '../data/processed/index_pipeline.csv',
        './data/processed/index_pipeline.csv'
    ]

    for path in paths:
        p = Path(path)
        if p.exists():
            return pd.read_csv(p)

    st.warning("No index data found. Run the pipeline first.")
    return None

@st.cache_data
def load_scores_data():
    """Load raw classification scores."""
    paths = [
        'data/processed/scores_pipeline.csv',
        '../data/processed/scores_pipeline.csv',
        './data/processed/scores_pipeline.csv'
    ]

    for path in paths:
        p = Path(path)
        if p.exists():
            return pd.read_csv(p)

    return None

# Load data
index_df = load_index_data()
scores_df = load_scores_data()

if index_df is None:
    st.error("❌ No data available. Please run the pipeline first.")
    st.info("Run: `python src/main.py --mode full` or `jupyter notebook notebooks/exploratory_analysis.ipynb`")
    st.stop()

# Convert date column
if 'date' in index_df.columns:
    index_df['date'] = pd.to_datetime(index_df['date'])

# Sidebar
st.sidebar.header("Controls")
time_period = st.sidebar.selectbox(
    "Time Period",
    ["All", "Last 30 Days", "Last 7 Days"]
)

# Filter data by time period
if time_period == "Last 7 Days":
    if len(index_df) > 7:
        filtered_df = index_df.iloc[-7:]
    else:
        filtered_df = index_df
elif time_period == "Last 30 Days":
    if len(index_df) > 30:
        filtered_df = index_df.iloc[-30:]
    else:
        filtered_df = index_df
else:
    filtered_df = index_df

# Main metrics
st.subheader("Key Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    current_index = filtered_df['index_value'].iloc[-1] if len(filtered_df) > 0 else 0
    st.metric(
        "Current Index",
        f"{current_index:.3f}",
        delta=f"{current_index - filtered_df['index_value'].iloc[-2] if len(filtered_df) > 1 else 0:.3f}",
        help="Current regulatory uncertainty level [0-1]"
    )

with col2:
    mean_index = filtered_df['index_value'].mean()
    st.metric(
        "Mean Uncertainty",
        f"{mean_index:.3f}",
        help="Average uncertainty over period"
    )

with col3:
    max_index = filtered_df['index_value'].max()
    st.metric(
        "Peak Uncertainty",
        f"{max_index:.3f}",
        help="Maximum uncertainty reached"
    )

with col4:
    if 'volatility' in filtered_df.columns:
        mean_vol = filtered_df['volatility'].mean()
        st.metric(
            "Mean Volatility",
            f"{mean_vol:.3f}",
            help="Average daily volatility"
        )

# Index timeseries chart
st.subheader("Uncertainty Index Timeline")

fig_index = go.Figure()

fig_index.add_trace(go.Scatter(
    x=filtered_df['date'] if 'date' in filtered_df.columns else range(len(filtered_df)),
    y=filtered_df['index_value'],
    mode='lines+markers',
    name='Index Value',
    line=dict(color='steelblue', width=2),
    marker=dict(size=6)
))

if 'smoothed_index' in filtered_df.columns:
    fig_index.add_trace(go.Scatter(
        x=filtered_df['date'] if 'date' in filtered_df.columns else range(len(filtered_df)),
        y=filtered_df['smoothed_index'],
        mode='lines',
        name='EMA Smoothed',
        line=dict(color='orange', width=2, dash='dash')
    ))

fig_index.update_layout(
    title="Regulatory Uncertainty Index",
    xaxis_title="Date",
    yaxis_title="Index Value",
    hovermode='x unified',
    height=400
)

st.plotly_chart(fig_index, use_container_width=True)

# Distribution charts
st.subheader("Score Distribution Analysis")

if scores_df is not None:
    col1, col2 = st.columns(2)

    with col1:
        # Histogram
        fig_hist = px.histogram(
            scores_df,
            x='score',
            nbins=20,
            title='Score Distribution',
            labels={'score': 'Uncertainty Score'},
            color_discrete_sequence=['steelblue']
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with col2:
        # Level counts
        level_counts = scores_df['uncertainty_level'].value_counts()
        colors = {
            'LOW': '#388e3c',
            'MODERATE': '#f57c00',
            'HIGH': '#d32f2f',
            'CRITICAL': '#7b1fa2'
        }

        fig_level = px.bar(
            x=level_counts.index,
            y=level_counts.values,
            title='Uncertainty Levels',
            labels={'x': 'Level', 'y': 'Count'},
            color=level_counts.index,
            color_discrete_map=colors
        )
        st.plotly_chart(fig_level, use_container_width=True)

# Domain analysis
st.subheader("Domain-Specific Analysis")

if scores_df is not None and 'regulatory_domain' in scores_df.columns:
    col1, col2 = st.columns(2)

    with col1:
        # Domain distribution
        domain_counts = scores_df['regulatory_domain'].value_counts()
        fig_domain = px.pie(
            values=domain_counts.values,
            names=domain_counts.index,
            title='Chunk Distribution by Domain'
        )
        st.plotly_chart(fig_domain, use_container_width=True)

    with col2:
        # Average score by domain
        domain_scores = scores_df.groupby('regulatory_domain')['score'].mean().sort_values(ascending=False)
        fig_domain_score = px.bar(
            x=domain_scores.index,
            y=domain_scores.values,
            title='Average Uncertainty by Domain',
            labels={'x': 'Domain', 'y': 'Average Score'},
            color=domain_scores.values,
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig_domain_score, use_container_width=True)

# Top uncertainty events
st.subheader("Top Uncertainty Events")

if scores_df is not None:
    top_n = st.slider("Show top N events:", 5, 20, 10)
    top_events = scores_df.nlargest(top_n, 'score')[
        ['chunk_id', 'score', 'confidence', 'uncertainty_level', 'regulatory_domain']
    ].reset_index(drop=True)

    # Color code by level
    def color_level(level):
        colors = {
            'LOW': 'background-color: #c8e6c9',
            'MODERATE': 'background-color: #ffe0b2',
            'HIGH': 'background-color: #ffcdd2',
            'CRITICAL': 'background-color: #f8bbd0'
        }
        return [colors.get(level, '')] * len(top_events.columns)

    st.dataframe(
        top_events.style.applymap(
            lambda x: 'color: #d32f2f; font-weight: bold;' if isinstance(x, float) and x > 0.7 else '',
            subset=['score']
        ),
        use_container_width=True
    )

# Statistics
st.subheader("Detailed Statistics")

col1, col2 = st.columns(2)

with col1:
    st.write("**Index Statistics**")
    if len(filtered_df) > 0:
        st.write(f"""
        - Mean: {filtered_df['index_value'].mean():.4f}
        - Std Dev: {filtered_df['index_value'].std():.4f}
        - Min: {filtered_df['index_value'].min():.4f}
        - Max: {filtered_df['index_value'].max():.4f}
        - Observations: {len(filtered_df)}
        """)

with col2:
    st.write("**Data Quality**")
    if scores_df is not None:
        st.write(f"""
        - Total chunks: {len(scores_df)}
        - Avg score: {scores_df['score'].mean():.4f}
        - Avg confidence: {scores_df['confidence'].mean():.4f}
        - Missing values: {scores_df.isnull().sum().sum()}
        - Domains: {scores_df['regulatory_domain'].nunique()}
        """)

# Info
st.sidebar.markdown("---")
st.sidebar.info("""
**About This Dashboard**

Monitors regulatory uncertainty index generated from:
- Federal Reserve statements
- SEC filings
- Regulatory documents
- Economic news

**Data Sources:**
- `data/processed/index_pipeline.csv`
- `data/processed/scores_pipeline.csv`

**Pipeline:**
Ingestion → Preprocessing → Embeddings → Classification → Index
""")

st.sidebar.markdown("---")
st.sidebar.write("**Built with:** Streamlit • Plotly • Pandas")
st.sidebar.write("**Version:** 1.0.0")
