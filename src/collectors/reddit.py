"""
Reddit post and comment collector.

Uses PRAW (Reddit API wrapper) for real-time data and
Arctic Shift / Pushshift archives for historical data.
"""

import logging
import time
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RedditPost:
    """Structured Reddit post/comment record."""
    title: str
    text: str
    subreddit: str
    url: str
    author: str = "[deleted]"
    score: int = 0
    num_comments: int = 0
    created_utc: Optional[float] = None
    post_type: str = "submission"  # "submission" or "comment"
    search_query: Optional[str] = None
    collected_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    @property
    def created_date(self) -> Optional[str]:
        if self.created_utc:
            return datetime.utcfromtimestamp(self.created_utc).isoformat()
        return None

    def to_dict(self):
        d = asdict(self)
        d["created_date"] = self.created_date
        return d


class RedditCollector:
    """Collect Reddit posts via PRAW (live API)."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str = "PharmaMisinfoTracker/1.0",
    ):
        try:
            import praw
        except ImportError:
            raise ImportError("Install praw: pip install praw")

        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )

    def search_subreddit(
        self,
        subreddit: str,
        query: str,
        sort: str = "relevance",
        time_filter: str = "all",
        limit: int = 100,
    ) -> List[RedditPost]:
        """
        Search a subreddit for posts matching a query.

        Args:
            subreddit: Subreddit name (without r/)
            query: Search string
            sort: "relevance", "hot", "top", "new", "comments"
            time_filter: "all", "year", "month", "week", "day"
            limit: Maximum posts to retrieve

        Returns:
            List of RedditPost objects
        """
        posts = []
        try:
            sub = self.reddit.subreddit(subreddit)
            results = sub.search(
                query, sort=sort, time_filter=time_filter, limit=limit
            )

            for submission in results:
                posts.append(RedditPost(
                    title=submission.title,
                    text=submission.selftext or "",
                    subreddit=subreddit,
                    url=f"https://reddit.com{submission.permalink}",
                    author=str(submission.author) if submission.author else "[deleted]",
                    score=submission.score,
                    num_comments=submission.num_comments,
                    created_utc=submission.created_utc,
                    post_type="submission",
                    search_query=query,
                ))

        except Exception as e:
            logger.error(f"Reddit search failed for r/{subreddit}: {e}")

        logger.info(
            f"Collected {len(posts)} posts from r/{subreddit} for '{query}'"
        )
        return posts

    def get_post_comments(
        self,
        post_url: str,
        limit: int = 50,
    ) -> List[RedditPost]:
        """Retrieve top-level comments from a specific post."""
        comments = []
        try:
            submission = self.reddit.submission(url=post_url)
            submission.comments.replace_more(limit=0)

            for comment in submission.comments[:limit]:
                comments.append(RedditPost(
                    title=submission.title,
                    text=comment.body,
                    subreddit=str(submission.subreddit),
                    url=f"https://reddit.com{comment.permalink}",
                    author=str(comment.author) if comment.author else "[deleted]",
                    score=comment.score,
                    created_utc=comment.created_utc,
                    post_type="comment",
                ))

        except Exception as e:
            logger.error(f"Failed to get comments: {e}")

        return comments


class ArcticShiftCollector:
    """
    Collect historical Reddit data via Arctic Shift API.
    Free, no authentication required.
    https://arctic-shift.photon-reddit.com/
    """

    BASE_URL = "https://arctic-shift.photon-reddit.com/api/posts/search"

    def __init__(self, wait_seconds: float = 1.0):
        self.wait_seconds = wait_seconds

    def search(
        self,
        query: str,
        subreddit: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        limit: int = 100,
    ) -> List[RedditPost]:
        """
        Search historical Reddit posts via Arctic Shift.

        Args:
            query: Search string
            subreddit: Limit to specific subreddit
            after: Start date (ISO format)
            before: End date (ISO format)
            limit: Maximum results

        Returns:
            List of RedditPost objects
        """
        import requests

        params = {"q": query, "limit": min(limit, 100)}
        if subreddit:
            params["subreddit"] = subreddit
        if after:
            params["after"] = after
        if before:
            params["before"] = before

        posts = []
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("data", []):
                posts.append(RedditPost(
                    title=item.get("title", ""),
                    text=item.get("selftext", ""),
                    subreddit=item.get("subreddit", ""),
                    url=f"https://reddit.com{item.get('permalink', '')}",
                    author=item.get("author", "[deleted]"),
                    score=item.get("score", 0),
                    num_comments=item.get("num_comments", 0),
                    created_utc=item.get("created_utc"),
                    post_type="submission",
                    search_query=query,
                ))

            time.sleep(self.wait_seconds)

        except Exception as e:
            logger.error(f"Arctic Shift search failed: {e}")

        logger.info(f"Collected {len(posts)} historical posts for '{query}'")
        return posts
