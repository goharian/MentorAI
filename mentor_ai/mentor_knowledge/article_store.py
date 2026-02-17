import logging

from django.apps import apps
from django.utils import timezone

logger = logging.getLogger(__name__)


def _parse_published_date(raw_date: str | None):
    if not raw_date:
        return None

    try:
        return timezone.datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
    except ValueError:
        logger.warning("Invalid publishedAt format; saving article without published_date: %s", raw_date)
        return None


def upsert_article(article_data: dict):
    # Keep legacy app label ("articles") for existing migrations/DB state.
    article_model = apps.get_model("articles", "Article")
    published_date = _parse_published_date(article_data.get("publishedAt"))

    article, created = article_model.objects.update_or_create(
        url=article_data["url"],
        defaults={
            "title": article_data["title"],
            "content": article_data.get("content", ""),
            "published_date": published_date,
            "source": article_data.get("source", {}).get("name", "N/A"),
        },
    )
    return article, created
