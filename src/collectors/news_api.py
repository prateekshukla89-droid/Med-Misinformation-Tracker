"""
News article collector using NewsAPI.org and Google News RSS.

Collects news articles mentioning specified pharmaceutical terms.
Free tier: 100 requests/day, up to 1 month back.
For historical data, falls back to Google News RSS + Wayback Machine.
"""

import logging
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Generator

import requests

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """Structured news article record."""
    title: str
    source: str
    url: str
    published_date: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    search_query: Optional[str] = None
    collected_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    def to_dict(self):
        return asdict(self)


class NewsAPICollector:
    """Collect news articles via NewsAPI.org."""

    BASE_URL = "https://newsapi.org/v2/everything"

    def __init__(self, api_key: str, wait_seconds: float = 1.0):
        self.api_key = api_key
        self.wait_seconds = wait_seconds

    def search(
        self,
        query: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        language: str = "en",
        sort_by: str = "relevancy",
        page_size: int = 100,
        max_pages: int = 5,
    ) -> List[NewsArticle]:
        """
        Search for news articles matching a query.

        Args:
            query: Search string
            from_date: Start date (ISO format). Free tier limited to ~1 month back.
            to_date: End date (ISO format)
            language: Language code
            sort_by: "relevancy", "popularity", or "publishedAt"
            page_size: Results per page (max 100)
            max_pages: Maximum pages to retrieve

        Returns:
            List of NewsArticle objects
        """
        articles = []

        for page in range(1, max_pages + 1):
            params = {
                "q": query,
                "language": language,
                "sortBy": sort_by,
                "pageSize": page_size,
                "page": page,
                "apiKey": self.api_key,
            }
            if from_date:
                params["from"] = from_date
            if to_date:
                params["to"] = to_date

            try:
                resp = requests.get(self.BASE_URL, params=params, timeout=30)
                resp.raise_for_status()
                data = resp.json()

                if data.get("status") != "ok":
                    logger.warning(f"NewsAPI error: {data.get('message')}")
                    break

                for item in data.get("articles", []):
                    articles.append(NewsArticle(
                        title=item.get("title", ""),
                        source=item.get("source", {}).get("name", ""),
                        url=item.get("url", ""),
                        published_date=item.get("publishedAt"),
                        description=item.get("description"),
                        content=item.get("content"),
                        search_query=query,
                    ))

                total_results = data.get("totalResults", 0)
                if page * page_size >= total_results:
                    break

                time.sleep(self.wait_seconds)

            except requests.RequestException as e:
                logger.error(f"NewsAPI request failed: {e}")
                break

        logger.info(f"Collected {len(articles)} articles for query: '{query}'")
        return articles


class GoogleNewsRSSCollector:
    """
    Collect news via Google News RSS feed.
    No API key required. Good for historical searches.
    """

    RSS_URL = "https://news.google.com/rss/search"

    def __init__(self, wait_seconds: float = 2.0):
        self.wait_seconds = wait_seconds

    def search(
        self,
        query: str,
        when: Optional[str] = None,
    ) -> List[NewsArticle]:
        """
        Search Google News RSS.

        Args:
            query: Search string
            when: Time filter (e.g., "1y" for past year, "6m" for 6 months)

        Returns:
            List of NewsArticle objects
        """
        try:
            import feedparser
        except ImportError:
            raise ImportError("Install feedparser: pip install feedparser")

        params = {"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"}
        if when:
            params["q"] += f" when:{when}"

        articles = []
        try:
            url = f"{self.RSS_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
            feed = feedparser.parse(url)

            for entry in feed.entries:
                articles.append(NewsArticle(
                    title=entry.get("title", ""),
                    source=entry.get("source", {}).get("title", "Google News"),
                    url=entry.get("link", ""),
                    published_date=entry.get("published"),
                    description=entry.get("summary"),
                    search_query=query,
                ))

        except Exception as e:
            logger.error(f"Google News RSS failed: {e}")

        logger.info(f"Collected {len(articles)} articles from Google News RSS")
        return articles
