"""
ChatGPT-based article summarization service.
"""
from django.conf import settings
from django.core.cache import caches
import logging
import openai


logger = logging.getLogger(__name__)
SUMMARY_CACHE = caches['summaries']


def summarize_article_with_chatgpt(title: str, content: str) -> str:
    """
    Returns a summary of the article using ChatGPT.

    :param title: The title of the article.
    :param content: The content of the article.
    :return: A summary string.
    """
    try:
        from openai import OpenAI, APIError 
        from openai._base_client import SyncHttpxClientWrapper
    except Exception:
        OpenAI = None
        APIError = Exception

    if not settings.OPENAI_API_KEY or OpenAI is None:
        if OpenAI is None and settings.OPENAI_API_KEY:
            logger.warning("OpenAI package not available — using fallback.")
        else:
            logger.warning("Missing API key — using fallback.")
        return f"**Mock Summary:** The article discusses {title}."

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        system_prompt = (
            "You are an expert news summarizer. "
            "Provide a concise, objective summary under 100 words."
        )

        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Title: {title}\n\nContent:\n{content}"}
            ],
            temperature=0.3,
            timeout=30
        )

        return response.output_text

    except APIError as e:
        logger.error(f"OpenAI API Error: {e}")
        return f"OpenAI API Error: {e}"
    except Exception as e:
        logger.exception("Unexpected error during summarization")
        return f"Unexpected summarization error: {e}"



def get_article_summary_with_caching(title: str, content: str):
    """
    Get article summary with caching.
    :param title: The title of the article.
    :param content: The content of the article.
    :return: A tuple of (summary string, from_cache boolean).
    """
    cache_key = f"summary:{title[:50]}"

    cached = SUMMARY_CACHE.get(cache_key)
    if cached is not None:
        return cached, True

    new_summary = summarize_article_with_chatgpt(title, content)
    SUMMARY_CACHE.set(cache_key, new_summary, timeout=86400)

    return new_summary, False
