from __future__ import annotations

import argparse
import os
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig


YOUTUBE_ID_LENGTH = 11
SUPPORTED_LANGUAGE = "en"


def _is_valid_video_id(video_id: str | None) -> bool:
    if not video_id or len(video_id) != YOUTUBE_ID_LENGTH:
        return False

    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
    return all(char in allowed_chars for char in video_id)


def get_video_id(youtube_url: str) -> str | None:
    """Extract a YouTube video ID from a URL or raw ID."""
    if not youtube_url:
        return None

    youtube_url = youtube_url.strip()

    # Support passing a raw video id directly.
    if _is_valid_video_id(youtube_url):
        return youtube_url

    parsed_url = urlparse(youtube_url)
    hostname = (parsed_url.hostname or "").lower()
    hostname = hostname.replace("www.", "").replace("m.", "")

    candidate: str | None = None
    path_parts = [part for part in parsed_url.path.split("/") if part]

    if hostname == "youtu.be" and path_parts:
        candidate = path_parts[0]
    elif hostname in {"youtube.com", "music.youtube.com"}:
        if path_parts and path_parts[0] in {"shorts", "embed", "live"} and len(path_parts) > 1:
            candidate = path_parts[1]
        else:
            candidate = parse_qs(parsed_url.query).get("v", [None])[0]

    return candidate if _is_valid_video_id(candidate) else None


def _join_transcript_entries(transcript_entries: list[dict]) -> str:
    return " ".join(entry.get("text", "").strip() for entry in transcript_entries if entry.get("text")).strip()


def _shorten_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text

    cut = text[:max_chars].rsplit(" ", 1)[0].strip()
    if not cut:
        cut = text[:max_chars].strip()
    return f"{cut}..."


def _validate_language(language: str) -> str | None:
    if (language or "").strip().lower() != SUPPORTED_LANGUAGE:
        return f"Only '{SUPPORTED_LANGUAGE}' is supported"
    return None


def _build_client() -> YouTubeTranscriptApi:
    proxy_username = os.getenv("YOUTUBE_PROXY_USER")
    proxy_password = os.getenv("YOUTUBE_PROXY_PASS")
    proxy_countries = os.getenv("YOUTUBE_PROXY_COUNTRIES", "")
    filter_ip_locations = [code.strip() for code in proxy_countries.split(",") if code.strip()]

    if proxy_username and proxy_password:
        proxy_config = WebshareProxyConfig(
            proxy_username=proxy_username,
            proxy_password=proxy_password,
            filter_ip_locations=filter_ip_locations or None,
        )
        return YouTubeTranscriptApi(proxy_config=proxy_config)

    return YouTubeTranscriptApi()


def get_transcript(youtube_url: str, language: str = SUPPORTED_LANGUAGE) -> dict:
    """Fetch transcript from YouTube and return a normalized response."""
    language_error = _validate_language(language)
    if language_error:
        return {"success": False, "error": language_error, "video_id": None}

    try:
        video_id = get_video_id(youtube_url)

        if not video_id:
            return {"success": False, "error": "Invalid YouTube URL", "video_id": None}

        transcript_entries = _build_client().fetch(
            video_id,
            languages=[SUPPORTED_LANGUAGE],
        ).to_raw_data()
        full_text = _join_transcript_entries(transcript_entries)

        return {
            "success": True,
            "video_id": video_id,
            "language": SUPPORTED_LANGUAGE,
            "transcript": full_text,
            "entries_count": len(transcript_entries),
            "entries": transcript_entries,
        }

    except Exception as exc:
        return {"success": False, "error": str(exc), "video_id": None}


def get_short_transcript(youtube_url: str, language: str = SUPPORTED_LANGUAGE, max_chars: int = 500) -> dict:
    """Fetch transcript and return a shortened text preview."""
    if max_chars <= 0:
        return {"success": False, "error": "max_chars must be a positive integer", "video_id": None}

    transcript_result = get_transcript(youtube_url, language=language)
    if not transcript_result.get("success"):
        return transcript_result

    full_text = transcript_result["transcript"]
    short_text = _shorten_text(full_text, max_chars=max_chars)

    return {
        **transcript_result,
        "short_transcript": short_text,
        "short_transcript_chars": len(short_text),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch a short transcript from a YouTube video URL")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--max-chars", type=int, default=500, help="Maximum characters for short transcript")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    result = get_short_transcript(args.url, max_chars=args.max_chars)
    if result.get("success"):
        print(result["short_transcript"])
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
