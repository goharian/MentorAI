import logging
import time

from celery import shared_task

from mentor_knowledge.article_store import upsert_article
from mentor_knowledge.models import VideoContent
from mentor_knowledge.video_processing_service import VideoProcessingService

logger = logging.getLogger(__name__)


@shared_task(name="mentor_knowledge.tasks.process_and_save_article_task")
def upsert_article_task(article_data):
    """
    Gets data from a single article and upserts it in the database.
    This function runs in a Celery Worker.
    """
    try:
        article, created = upsert_article(article_data)
    except LookupError:
        logger.warning("Article model is not available; skipping article task.")
        return False
    except Exception as exc:
        logger.error(
            "Error processing or saving article in Celery: %s - URL: %s",
            exc,
            article_data.get("url"),
        )
        raise

    if created:
        logger.info("Article saved successfully: %s", article.url)
    else:
        logger.info("Article updated: %s", article.url)

    return created


# Backward-compatible alias for existing imports.
process_and_save_article_task = upsert_article_task


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    dont_autoretry_for=(ValueError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def process_video_transcript_task(self, video_id: str):
    """
    Pull transcript + process chunks/embeddings in a Celery worker.
    """
    start_time = time.perf_counter()
    logger.info(
        "Video transcript processing started | task_id=%s video_id=%s retries=%s",
        self.request.id,
        video_id,
        self.request.retries,
    )

    try:
        video = VideoContent.objects.select_related("mentor").get(id=video_id)
    except VideoContent.DoesNotExist:
        logger.error("VideoContent not found for processing: %s", video_id)
        return {"video_id": video_id, "status": "not_found", "skipped": True}

    if video.status == VideoContent.Status.READY:
        logger.info("Video %s already ready; skipping.", video_id)
        return {"video_id": video_id, "status": video.status, "skipped": True}

    try:
        service = VideoProcessingService()
        result = service.process_video_from_youtube(video)
        duration = time.perf_counter() - start_time
        logger.info(
            "Video transcript processing completed | task_id=%s video_id=%s duration_sec=%.2f chunks_created=%s transcript_entries=%s",
            self.request.id,
            video_id,
            duration,
            result.get("chunks_created"),
            result.get("transcript_entries"),
        )
        video.refresh_from_db(fields=["status"])
        return {"video_id": video_id, "status": video.status, **result}
    except Exception:
        VideoContent.objects.filter(id=video_id).update(status=VideoContent.Status.FAILED)
        duration = time.perf_counter() - start_time
        logger.exception(
            "Video transcript processing failed | task_id=%s video_id=%s duration_sec=%.2f",
            self.request.id,
            video_id,
            duration,
        )
        raise

