from django.db import IntegrityError, transaction
from django.test import TestCase

from mentor_knowledge.models import ContentChunk, Mentor, VideoContent


class ModelsTests(TestCase):
    def setUp(self):
        self.mentor = Mentor.objects.create(
            name="Naval Ravikant",
            slug="naval-ravikant",
        )

    def test_mentor_str_returns_name(self):
        self.assertEqual(str(self.mentor), "Naval Ravikant")

    def test_video_content_unique_per_mentor_and_youtube_id(self):
        VideoContent.objects.create(
            mentor=self.mentor,
            title="How to Build Products",
            youtube_video_id="dQw4w9WgXcQ",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                VideoContent.objects.create(
                    mentor=self.mentor,
                    title="Duplicate Video",
                    youtube_video_id="dQw4w9WgXcQ",
                )

    def test_content_chunk_unique_chunk_index_per_video(self):
        video = VideoContent.objects.create(
            mentor=self.mentor,
            title="Learning in Public",
            youtube_video_id="xvFZjo5PgG0",
        )
        ContentChunk.objects.create(
            video=video,
            chunk_index=0,
            text="first chunk",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ContentChunk.objects.create(
                    video=video,
                    chunk_index=0,
                    text="duplicate chunk index",
                )

