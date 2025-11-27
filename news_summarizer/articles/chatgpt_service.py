"""
ChatGPT-based article summarization service.
"""
import hashlib
from django.conf import settings
from django.core.cache import caches
import logging
import openai


logger = logging.getLogger(__name__)
SUMMARY_CACHE = caches['summaries']

def _generate_cache_key(title: str, content: str) -> str:
    """
    Generate a unique cache key for the article summary.
    :param title: The title of the article.
    :param content: The content of the article.
    :return: A unique cache key string.
    """
    unique_string = f"{title}:{content}"
    hash_key = hashlib.md5(unique_string.encode('utf-8')).hexdigest()
    return f"summary:{hash_key}"

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

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Title: {title}\n\nContent:\n{content}"}
            ],
            temperature=0.3,
            timeout=30
        )

        return response.choices[0].message.content.strip()

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
    cache_key = _generate_cache_key(title, content)

    cached = SUMMARY_CACHE.get(cache_key)
    if cached is not None:
        logger.info(f"Cache HIT for {cache_key}")
        return cached, True

    logger.info(f"Cache MISS for {cache_key}. Generating new summary.")
    new_summary = summarize_article_with_chatgpt(title, content)

    # Store in cache for 24 hours
    SUMMARY_CACHE.set(cache_key, new_summary, timeout=86400)

    return new_summary, False
