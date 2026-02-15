from __future__ import annotations

import argparse
import json
from pathlib import Path

from articles.youtube_transcript import get_transcript


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch full English transcript from a YouTube URL")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument(
        "--output",
        default="full_transcript.txt",
        help="Output text file path (default: full_transcript.txt)",
    )
    parser.add_argument(
        "--json-output",
        default="",
        help="Optional JSON output path with metadata and entries",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = get_transcript(args.url)

    if not result.get("success"):
        print(f"Error: {result.get('error', 'Unknown error')}")
        return 1

    output_path = Path(args.output)
    output_path.write_text(result["transcript"], encoding="utf-8")
    print(f"Saved full transcript to: {output_path}")
    print(f"Video ID: {result['video_id']} | Entries: {result['entries_count']}")

    if args.json_output:
        json_path = Path(args.json_output)
        json_payload = {
            "video_id": result["video_id"],
            "language": result["language"],
            "entries_count": result["entries_count"],
            "entries": result["entries"],
        }
        json_path.write_text(json.dumps(json_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved JSON metadata to: {json_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
