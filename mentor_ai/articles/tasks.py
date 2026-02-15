import logging
from celery import shared_task
from django.apps import apps
from django.utils import timezone

from articles.models import VideoContent
from articles.video_processing_service import VideoProcessingService

logger = logging.getLogger(__name__)

# ההערה @shared_task הופכת את הפונקציה למשימת Celery אסינכרונית
@shared_task
def process_and_save_article_task(article_data):
    """
    Gets data from a single article and saves it to the Database.
    This function runs in a Celery Worker.
    """
    try:
        try:
            Article = apps.get_model("articles", "Article")
        except LookupError:
            logger.warning("Article model is not available; skipping article task.")
            return False

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


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def process_video_transcript_task(self, video_id: str):
    """
    Pull transcript + process chunks/embeddings in a Celery worker.
    """
    try:
        video = VideoContent.objects.select_related("mentor").get(id=video_id)
    except VideoContent.DoesNotExist as exc:
        logger.error("VideoContent not found for processing: %s", video_id)
        raise ValueError(f"VideoContent not found: {video_id}") from exc

    if video.status == VideoContent.Status.READY:
        logger.info("Video %s already ready; skipping.", video_id)
        return {"video_id": video_id, "status": video.status, "skipped": True}

    try:
        service = VideoProcessingService()
        result = service.process_video_from_youtube(video)
        logger.info("Video transcript processing completed: %s", video_id)
        return {"video_id": video_id, "status": video.status, **result}
    except Exception as exc:
        VideoContent.objects.filter(id=video_id).update(status=VideoContent.Status.FAILED)
        logger.exception("Video transcript processing failed: %s", video_id)
        raise exc
