"""
Handles the external logic.
"""
import logging
from venv import logger
import requests
from django.conf import settings
from django.utils import timezone
from requests.exceptions import RequestException

from articles.models import Article

logger = logging.getLogger(__name__)

def fetch_and_store_articles():
    """
    Fetch articles from NewsAPI and store them in the database.
    """
    logger.info("Starting to fetch new articles from NewsAPI...")
    api_url = settings.NEWS_API_URL
    api_key = settings.NEWS_API_KEY
    query = settings.NEWS_API_QUERY

    params = {
        'q': query,
        'language': 'en',
        'sortBy': 'publishedAt',
        'apiKey': api_key,
    }

    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except RequestException as e:
        logger.error(f"Error calling News API: {e}")
        return
    
    articles_saved = 0
    articles_skipped = 0

    for article_data in data.get('articles', []):
        try:
            published_date = timezone.datetime.fromisoformat(article_data['publishedAt'].replace('Z', '+00:00'))

            article, created = Article.objects.update_or_create(
                url=article_data['url'],
                defaults={
                    'title': article_data['title'],
                    'content': article_data.get('content', ''),
                    'published_date': published_date,
                    'source': article_data.get('source', {}).get('name', 'N/A')
                }
            )
            
            if created:
                articles_saved += 1
            else:
                articles_skipped += 1

        except Exception as e:
            logger.error(f"Error processing or saving article: {e} - URL: {article_data.get('url')}")
            
    logger.info(f"Finished pulling articles. Saved: {articles_saved}, skipped/updated: {articles_skipped}")
    return articles_saved