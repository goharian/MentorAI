"""
Handles the external news fetching logic.
"""
import logging
import requests
from django.conf import settings
from django.utils import timezone
from requests.exceptions import RequestException
from articles.models import Article
from articles.tasks import process_and_save_article_task

# Set up logging
logger = logging.getLogger(__name__)

class NewsApiClient:
    """
    Docstring for NewsApiClient
    """
    def __init__(self):
        self.api_url = settings.NEWS_API_URL
        self.api_key = settings.NEWS_API_KEY
        self.query = settings.NEWS_API_QUERY
    
    def fetch_articles(self):
        """
        Docstring for fetch_articles
        
        :param self: Description
        """
        params = {
            'q': self.query,
            'language': 'en',
            'sortBy': 'publishedAt',
            'apiKey': self.api_key,
        }

        try:
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('articles', [])
        except RequestException as e:
            logger.error(f"Error calling News API: {e}")
            return []


class ArticleService:
    """
    Docstring for ArticleService
    """
    def process_and_save_article(self, article_data):
        try:
            # טיפול בתאריך
            raw_date = article_data.get('publishedAt')
            published_date = None
            if raw_date:
                published_date = timezone.datetime.fromisoformat(raw_date.replace('Z', '+00:00'))

            # שמירה או עדכון ב-DB
            article, created = Article.objects.update_or_create(
                url=article_data['url'],
                defaults={
                    'title': article_data['title'],
                    'content': article_data.get('content', ''),
                    'published_date': published_date,
                    'source': article_data.get('source', {}).get('name', 'N/A')
                }
            )
            return created

        except Exception as e:
            logger.error(f"Error processing or saving article: {e} - URL: {article_data.get('url')}")
            return False

def fetch_and_store_articles():
    """
   The main function that manages the process:
    1. Fetch data using the Client.
    2. Send data for background processing using Celery.
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
            process_and_save_article_task.delay(article_data) 
            articles_queued += 1
        except Exception as e:
            logger.error(f"Failed to queue article for processing: {e} - URL: {article_data.get('url')}")

    logger.info(f"Finished pulling articles. {articles_queued} articles sent to Celery queue.")
    
    return articles_queued