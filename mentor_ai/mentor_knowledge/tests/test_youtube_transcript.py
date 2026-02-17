from unittest import mock

from django.test import SimpleTestCase

from mentor_knowledge.youtube_transcript import get_short_transcript, get_transcript, get_video_id


class YouTubeTranscriptTests(SimpleTestCase):
    def test_get_video_id_from_watch_url(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.assertEqual(get_video_id(url), "dQw4w9WgXcQ")

    def test_get_video_id_from_shorts_url(self):
        url = "https://youtube.com/shorts/dQw4w9WgXcQ?feature=share"
        self.assertEqual(get_video_id(url), "dQw4w9WgXcQ")

    def test_get_video_id_invalid_url(self):
        self.assertIsNone(get_video_id("https://example.com/video"))

    @mock.patch("mentor_knowledge.youtube_transcript._build_client")
    def test_get_transcript_success(self, mock_build_client):
        mock_client = mock.Mock()
        mock_fetch_result = mock.Mock()
        mock_fetch_result.to_raw_data.return_value = [
            {"text": "Hello", "start": 0.0, "duration": 1.0},
            {"text": "world", "start": 1.0, "duration": 1.0},
        ]
        mock_client.fetch.return_value = mock_fetch_result
        mock_build_client.return_value = mock_client

        result = get_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        self.assertTrue(result["success"])
        self.assertEqual(result["video_id"], "dQw4w9WgXcQ")
        self.assertEqual(result["language"], "en")
        self.assertEqual(result["transcript"], "Hello world")
        self.assertEqual(result["entries_count"], 2)

    def test_get_transcript_rejects_non_en_language(self):
        result = get_transcript(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            language="he",
        )

        self.assertFalse(result["success"])
        self.assertIn("Only 'en'", result["error"])

    @mock.patch("mentor_knowledge.youtube_transcript._build_client")
    def test_get_short_transcript_truncates(self, mock_build_client):
        mock_client = mock.Mock()
        mock_fetch_result = mock.Mock()
        mock_fetch_result.to_raw_data.return_value = [
            {"text": "This is a very long sentence for testing transcript shortening logic."}
        ]
        mock_client.fetch.return_value = mock_fetch_result
        mock_build_client.return_value = mock_client

        result = get_short_transcript(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            max_chars=20,
        )

        self.assertTrue(result["success"])
        self.assertTrue(result["short_transcript"].endswith("..."))
        self.assertLessEqual(result["short_transcript_chars"], 23)

    def test_get_short_transcript_invalid_max_chars(self):
        result = get_short_transcript(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            max_chars=0,
        )

        self.assertFalse(result["success"])
        self.assertIn("max_chars", result["error"])

