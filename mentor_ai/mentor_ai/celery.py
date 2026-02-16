import os
import logging
import time

from celery import Celery
from celery.signals import task_failure, task_postrun, task_prerun, task_retry

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mentor_ai.settings')

app = Celery('mentor_ai')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

logger = logging.getLogger("mentor_ai.celery_monitor")
task_started_at = {}


def _load_heavy_task_names():
    names = os.getenv(
        "CELERY_HEAVY_TASK_NAMES",
        "articles.tasks.process_video_transcript_task",
    )
    return {name.strip() for name in names.split(",") if name.strip()}


def _load_heavy_task_threshold_seconds():
    try:
        return float(os.getenv("CELERY_HEAVY_TASK_THRESHOLD_SECONDS", "30"))
    except ValueError:
        return 30.0


heavy_task_names = _load_heavy_task_names()
heavy_task_threshold_seconds = _load_heavy_task_threshold_seconds()


def _is_heavy_task(task_name):
    return task_name in heavy_task_names


def _task_duration(task_id):
    started = task_started_at.get(task_id)
    if started is None:
        return None
    return time.perf_counter() - started


@task_prerun.connect
def log_heavy_task_start(task_id=None, task=None, args=None, kwargs=None, **_):
    if not task or not _is_heavy_task(task.name):
        return

    task_started_at[task_id] = time.perf_counter()
    logger.info(
        "Heavy task started | task_name=%s task_id=%s retries=%s args_count=%s kwargs_keys=%s",
        task.name,
        task_id,
        getattr(getattr(task, "request", None), "retries", 0),
        len(args or ()),
        sorted((kwargs or {}).keys()),
    )


@task_retry.connect
def log_heavy_task_retry(request=None, reason=None, **_):
    if request is None or not _is_heavy_task(getattr(request, "task", "")):
        return

    logger.warning(
        "Heavy task retry scheduled | task_name=%s task_id=%s retries=%s reason=%s",
        request.task,
        request.id,
        request.retries,
        reason,
    )


@task_failure.connect
def log_heavy_task_failure(task_id=None, exception=None, sender=None, **_):
    task_name = getattr(sender, "name", None)
    if not task_name or not _is_heavy_task(task_name):
        return

    duration = _task_duration(task_id)
    logger.error(
        "Heavy task failed | task_name=%s task_id=%s duration_sec=%s error=%s",
        task_name,
        task_id,
        f"{duration:.2f}" if duration is not None else "n/a",
        exception,
    )


@task_postrun.connect
def log_heavy_task_finish(task_id=None, task=None, state=None, **_):
    if not task or not _is_heavy_task(task.name):
        return

    duration = _task_duration(task_id)
    task_started_at.pop(task_id, None)
    if duration is None:
        return

    log_message = (
        "Heavy task completed | task_name=%s task_id=%s state=%s duration_sec=%.2f"
    )
    if duration >= heavy_task_threshold_seconds:
        logger.warning(log_message, task.name, task_id, state, duration)
        return

    logger.info(log_message, task.name, task_id, state, duration)

@app.task(bind=True)
def debug_task(self):
    logger.debug("Debug task request: %r", self.request)
