"""
Handles the external news fetching logic.
"""

import logging

import requests
from django.conf import settings
from requests.exceptions import RequestException

from mentor_knowledge.article_store import upsert_article
from mentor_knowledge.tasks import upsert_article_task

logger = logging.getLogger(__name__)


class NewsApiClient:
    """Client for fetching articles from NewsAPI."""

    def __init__(self):
        self.api_url = settings.NEWS_API_URL
        self.api_key = settings.NEWS_API_KEY
        self.query = settings.NEWS_API_QUERY

    def fetch_articles(self):
        params = {
            "q": self.query,
            "language": "en",
            "sortBy": "publishedAt",
            "apiKey": self.api_key,
        }

        try:
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("articles", [])
        except RequestException as exc:
            logger.error("Error calling News API: %s", exc)
            return []


class ArticleService:
    """Service for upserting article payloads into the database."""

    def upsert_article(self, article_data):
        try:
            _article, created = upsert_article(article_data)
            return created
        except LookupError:
            logger.warning("Article model is not available; skipping article upsert.")
            return False
        except Exception as exc:
            logger.error(
                "Error processing or saving article: %s - URL: %s",
                exc,
                article_data.get("url"),
            )
            return False

    # Backward-compatible method name.
    def process_and_save_article(self, article_data):
        return self.upsert_article(article_data)


def fetch_and_store_articles():
    """
    Main pipeline:
    1. Fetch data from NewsAPI.
    2. Send each article for background upsert via Celery.
    """
    logger.info("Starting to fetch new articles from NewsAPI...")

    client = NewsApiClient()
    articles_data = client.fetch_articles()

    if not articles_data:
        logger.warning("No articles found or API failed.")
        return 0

    articles_queued = 0

    for article_data in articles_data:
        try:
            upsert_article_task.delay(article_data)
            articles_queued += 1
        except Exception as exc:
            logger.error(
                "Failed to queue article for processing: %s - URL: %s",
                exc,
                article_data.get("url"),
            )

    logger.info("Finished pulling articles. %s articles sent to Celery queue.", articles_queued)

    return articles_queued

