import logging
from celery import shared_task
from django.utils import timezone

from articles.models import Article

logger = logging.getLogger(__name__)

# ההערה @shared_task הופכת את הפונקציה למשימת Celery אסינכרונית
@shared_task
def process_and_save_article_task(article_data):
    """
    Gets data from a single article and saves it to the Database.
    This function runs in a Celery Worker.
    """
    try:
        raw_date = article_data.get('publishedAt')
        published_date = None
        if raw_date:
            published_date = timezone.datetime.fromisoformat(raw_date.replace('Z', '+00:00'))

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
            logger.info(f"Article saved successfully: {article.url}")
        else:
            logger.info(f"Article updated/skipped: {article.url}")

        return created # Return True whether a new article was created

    except Exception as e:
        logger.error(f"Error processing or saving article in Celery: {e} - URL: {article_data.get('url')}")
        # It's important not to return anything to allow Celery to handle the error
        raise