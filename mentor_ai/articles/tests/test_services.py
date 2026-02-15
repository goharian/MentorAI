from unittest import mock

from django.test import TestCase

from articles.chunking_service import ChunkData
from articles.models import ContentChunk, Mentor, VideoContent
from articles.video_processing_service import VideoProcessingService


class VideoProcessingServiceTests(TestCase):
    def setUp(self):
        self.embedding_service_patcher = mock.patch("articles.video_processing_service.EmbeddingService")
        self.embedding_service_patcher.start()
        self.mentor = Mentor.objects.create(
            name="Test Mentor",
            slug="test-mentor",
        )
        self.video = VideoContent.objects.create(
            mentor=self.mentor,
            title="A long enough title",
            youtube_video_id="dQw4w9WgXcQ",
        )

    def tearDown(self):
        self.embedding_service_patcher.stop()

    @mock.patch("articles.video_processing_service.get_transcript")
    def test_process_video_from_youtube_raises_on_fetch_error(self, mock_get_transcript):
        mock_get_transcript.return_value = {
            "success": False,
            "error": "Transcript disabled",
        }
        service = VideoProcessingService()

        with self.assertRaises(ValueError):
            service.process_video_from_youtube(self.video)

        self.video.refresh_from_db()
        self.assertEqual(self.video.status, VideoContent.Status.NEW)

    @mock.patch("articles.video_processing_service.get_transcript")
    def test_process_video_from_youtube_calls_process_with_entries(self, mock_get_transcript):
        mock_get_transcript.return_value = {
            "success": True,
            "entries_count": 2,
            "entries": [
                {"text": "hello", "start": 0.0, "duration": 1.0},
                {"text": "world", "start": 1.0, "duration": 1.0},
            ],
        }
        service = VideoProcessingService()
        service.process_video_with_transcript = mock.Mock(
            return_value={"success": True, "chunks_created": 1, "total_duration": 2.0}
        )

        result = service.process_video_from_youtube(self.video)

        self.video.refresh_from_db()
        self.assertEqual(self.video.status, VideoContent.Status.FETCHED)
        self.assertEqual(result["transcript_entries"], 2)
        service.process_video_with_transcript.assert_called_once()

    def test_process_video_with_transcript_replaces_old_chunks(self):
        ContentChunk.objects.create(
            video=self.video,
            chunk_index=0,
            text="old chunk",
        )
        service = VideoProcessingService()
        service.chunker = mock.Mock(
            chunk_transcript=mock.Mock(
                return_value=[
                    ChunkData(
                        text="new chunk",
                        chunk_index=0,
                        start_seconds=0.0,
                        end_seconds=2.0,
                        word_count=2,
                    )
                ]
            )
        )
        service._create_chunks_with_embeddings = mock.Mock()

        result = service.process_video_with_transcript(
            self.video,
            [{"text": "new chunk", "start": 0.0, "duration": 2.0}],
        )

        self.video.refresh_from_db()
        self.assertEqual(self.video.status, VideoContent.Status.READY)
        self.assertEqual(result["chunks_created"], 1)
        self.assertEqual(ContentChunk.objects.filter(video=self.video).count(), 0)
