"""
Google Trends data collector.

Collects search interest time series for drug-related keywords.
No API key required — uses the pytrends library.
"""

import time
import logging
from datetime import datetime
from typing import List, Optional, Dict

import pandas as pd

logger = logging.getLogger(__name__)


class GoogleTrendsCollector:
    """Collect Google Trends data for pharmaceutical misinformation keywords."""

    def __init__(self, geo: str = "US", wait_seconds: float = 2.0):
        """
        Args:
            geo: Geographic region code (default: US)
            wait_seconds: Delay between requests to avoid rate limiting
        """
        try:
            from pytrends.request import TrendReq
        except ImportError:
            raise ImportError("Install pytrends: pip install pytrends")

        self.pytrends = TrendReq(hl="en-US", tz=360)
        self.geo = geo
        self.wait_seconds = wait_seconds

    def collect_interest_over_time(
        self,
        keywords: List[str],
        timeframe: str = "2019-01-01 2025-12-31",
        category: int = 0,
    ) -> pd.DataFrame:
        """
        Collect search interest over time for given keywords.

        Args:
            keywords: List of search terms (max 5 per request)
            timeframe: Date range string (e.g., "2019-01-01 2025-12-31")
            category: Google Trends category ID (0 = all)

        Returns:
            DataFrame with date index and keyword columns (0-100 scale)
        """
        all_data = pd.DataFrame()

        # Google Trends allows max 5 keywords per request
        for i in range(0, len(keywords), 5):
            batch = keywords[i:i + 5]
            logger.info(f"Fetching trends for: {batch}")

            try:
                self.pytrends.build_payload(
                    batch,
                    cat=category,
                    timeframe=timeframe,
                    geo=self.geo,
                )
                data = self.pytrends.interest_over_time()

                if not data.empty:
                    data = data.drop(columns=["isPartial"], errors="ignore")
                    all_data = pd.concat([all_data, data], axis=1)

                time.sleep(self.wait_seconds)

            except Exception as e:
                logger.warning(f"Failed to fetch trends for {batch}: {e}")

        return all_data

    def collect_related_queries(
        self,
        keyword: str,
        timeframe: str = "2019-01-01 2025-12-31",
    ) -> Dict[str, pd.DataFrame]:
        """
        Collect related queries (rising and top) for a keyword.

        Returns:
            Dict with 'top' and 'rising' DataFrames
        """
        self.pytrends.build_payload(
            [keyword], timeframe=timeframe, geo=self.geo
        )
        related = self.pytrends.related_queries()

        result = {}
        if keyword in related:
            result["top"] = related[keyword].get("top", pd.DataFrame())
            result["rising"] = related[keyword].get("rising", pd.DataFrame())

        return result

    def detect_spike(
        self,
        data: pd.DataFrame,
        keyword: str,
        threshold_std: float = 2.0,
    ) -> pd.DataFrame:
        """
        Detect significant spikes in search interest.

        Args:
            data: Trends DataFrame
            keyword: Column name to analyze
            threshold_std: Number of standard deviations above mean to flag

        Returns:
            DataFrame of spike dates with magnitude
        """
        if keyword not in data.columns:
            raise ValueError(f"Keyword '{keyword}' not in data columns")

        series = data[keyword]
        mean_val = series.mean()
        std_val = series.std()
        threshold = mean_val + (threshold_std * std_val)

        spikes = data[series > threshold].copy()
        spikes["magnitude"] = (spikes[keyword] - mean_val) / std_val

        return spikes[[keyword, "magnitude"]]
