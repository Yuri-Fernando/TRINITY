"""
Regulatory Uncertainty Index generation and aggregation.

Creates time-series indices from uncertainty scores using probabilistic
aggregation and temporal smoothing.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from loguru import logger


@dataclass
class IndexDatapoint:
    """Single datapoint in the uncertainty index."""
    timestamp: datetime
    index_value: float
    component_scores: Dict[str, float]  # Domain-specific scores
    signal_count: int
    document_count: int
    uncertainty_distribution: Dict  # Distribution of uncertainty levels


class UncertaintyIndex:
    """
    Generates regulatory uncertainty index from uncertainty scores.

    Aggregation strategy:
    1. Weighted average of scores (higher weights for recent, relevant docs)
    2. Domain-specific sub-indices
    3. Temporal smoothing with exponential moving average (EMA)
    4. Volatility measurement using rolling standard deviation
    """

    def __init__(self, smoothing_window: int = 7, decay_factor: float = 0.7):
        """
        Initialize index generator.

        Args:
            smoothing_window: Number of days for rolling window
            decay_factor: Weight decay for older documents (0-1)
        """
        self.smoothing_window = smoothing_window
        self.decay_factor = decay_factor
        logger.info(f"Initialized UncertaintyIndex (window={smoothing_window}, decay={decay_factor})")

    def compute_index(
        self,
        scores_df: pd.DataFrame,
        domain: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Compute uncertainty index from scores dataframe.

        Expected DataFrame columns:
        - timestamp: datetime
        - score: float [0-1]
        - confidence: float [0-1]
        - uncertainty_level: str
        - regulatory_domain: str

        Args:
            scores_df: DataFrame with classification scores
            domain: Optional domain filter (e.g., 'credit', 'market')

        Returns:
            DataFrame with index values and components
        """
        df = scores_df.copy()

        # Filter by domain if specified
        if domain:
            df = df[df["regulatory_domain"] == domain]
            logger.info(f"Filtered to domain: {domain} ({len(df)} documents)")

        # Ensure timestamp is datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Sort by timestamp
        df = df.sort_values("timestamp")

        # Add time decay weights (recent documents weighted higher)
        max_date = df["timestamp"].max()
        df["days_ago"] = (max_date - df["timestamp"]).dt.days
        df["time_weight"] = self.decay_factor ** (df["days_ago"] / 30)  # Decay over 30 days

        # Combine score and confidence weights
        df["weight"] = df["score"] * df["confidence"] * df["time_weight"]

        # Normalize weights
        df["weight"] = df["weight"] / df["weight"].sum()

        # Compute weighted index
        index_value = (df["score"] * df["weight"]).sum()

        logger.info(f"Computed index: {index_value:.4f}")

        return {
            "index_value": index_value,
            "documents_count": len(df),
            "avg_confidence": df["confidence"].mean(),
            "weighted_scores": df[["timestamp", "score", "weight"]].values.tolist()
        }

    def compute_rolling_index(
        self,
        scores_df: pd.DataFrame,
        window_days: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Compute rolling uncertainty index over time.

        Args:
            scores_df: DataFrame with classification scores
            window_days: Rolling window size (default: self.smoothing_window)

        Returns:
            DataFrame with daily index values
        """
        window = window_days or self.smoothing_window
        df = scores_df.copy()

        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")

        # Set date index
        df = df.set_index("timestamp")

        # Resample to daily and compute index
        daily_index = []

        for date in pd.date_range(df.index.min(), df.index.max(), freq='D'):
            window_start = date - timedelta(days=window)
            window_end = date

            window_data = df[(df.index >= window_start) & (df.index <= window_end)]

            if len(window_data) == 0:
                index_value = np.nan
                signal_count = 0
                doc_count = 0
            else:
                # Compute weighted index for window
                window_data["weight"] = window_data["confidence"]
                window_data["weight"] = window_data["weight"] / window_data["weight"].sum()
                index_value = (window_data["score"] * window_data["weight"]).sum()
                signal_count = window_data["uncertainty_level"].isin(["HIGH", "CRITICAL"]).sum()
                doc_count = len(window_data)

            daily_index.append({
                "date": date,
                "index_value": index_value,
                "signal_count": signal_count,
                "document_count": doc_count
            })

        result_df = pd.DataFrame(daily_index)
        logger.info(f"Computed rolling index for {len(result_df)} days")

        return result_df

    def apply_exponential_smoothing(
        self,
        index_series: pd.Series,
        alpha: float = 0.3
    ) -> pd.Series:
        """
        Apply exponential moving average smoothing.

        Args:
            index_series: Series of index values
            alpha: Smoothing factor (0-1)

        Returns:
            Smoothed series
        """
        ema = index_series.ewm(alpha=alpha).mean()
        logger.debug(f"Applied EMA smoothing (alpha={alpha})")
        return ema

    def compute_volatility(
        self,
        index_series: pd.Series,
        window: int = 30
    ) -> pd.Series:
        """
        Compute rolling volatility (std deviation).

        Args:
            index_series: Series of index values
            window: Rolling window size in days

        Returns:
            Series of volatility values
        """
        volatility = index_series.rolling(window=window).std()
        logger.debug(f"Computed rolling volatility (window={window})")
        return volatility

    def compute_domain_components(
        self,
        scores_df: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Compute domain-specific sub-indices.

        Args:
            scores_df: DataFrame with classification scores

        Returns:
            Dict mapping domain names to index values
        """
        df = scores_df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        domain_indices = {}

        for domain in df["regulatory_domain"].unique():
            if pd.isna(domain):
                continue

            domain_df = df[df["regulatory_domain"] == domain]
            index_val = (domain_df["score"] * domain_df["confidence"]).sum() / len(domain_df)

            domain_indices[domain] = index_val

        logger.info(f"Computed indices for {len(domain_indices)} domains")
        return domain_indices


class IndexingPipeline:
    """End-to-end pipeline for uncertainty index generation."""

    def __init__(self, smoothing_window: int = 7):
        self.index_generator = UncertaintyIndex(smoothing_window=smoothing_window)

    def process_scores(self, scores: List[Dict]) -> Tuple[float, pd.DataFrame]:
        """
        Process uncertainty scores into index.

        Args:
            scores: List of score dictionaries

        Returns:
            (overall_index_value, rolling_index_df)
        """
        # Convert to DataFrame
        df = pd.DataFrame(scores)

        # Compute overall index
        overall_index = self.index_generator.compute_index(df)

        # Compute rolling index
        rolling_index = self.index_generator.compute_rolling_index(df)

        # Apply smoothing
        rolling_index["smoothed_index"] = self.index_generator.apply_exponential_smoothing(
            rolling_index["index_value"]
        )

        # Compute volatility
        rolling_index["volatility"] = self.index_generator.compute_volatility(
            rolling_index["index_value"],
            window=30
        )

        logger.info(f"Generated index pipeline output: {len(rolling_index)} daily datapoints")

        return overall_index["index_value"], rolling_index

    def export_index(self, index_df: pd.DataFrame, output_path: str) -> None:
        """Export index to CSV."""
        index_df.to_csv(output_path, index=False)
        logger.info(f"Exported index to {output_path}")


if __name__ == "__main__":
    # Example usage
    sample_scores = [
        {
            "timestamp": datetime.now() - timedelta(days=i),
            "score": 0.3 + 0.1 * np.sin(i / 5),
            "confidence": 0.85,
            "uncertainty_level": "MODERATE",
            "regulatory_domain": "credit"
        }
        for i in range(30)
    ]

    df = pd.DataFrame(sample_scores)
    index_gen = UncertaintyIndex()
    overall = index_gen.compute_index(df)
    rolling = index_gen.compute_rolling_index(df)

    print(f"Overall index: {overall['index_value']:.4f}")
    print(f"Rolling index shape: {rolling.shape}")
