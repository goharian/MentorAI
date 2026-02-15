from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from articles.models import ContentChunk, Mentor, VideoContent


class ArticlesApiViewsTests(APITestCase):
    def setUp(self):
        self.mentor = Mentor.objects.create(
            name="Naval Ravikant",
            slug="naval-ravikant",
        )
        self.video = VideoContent.objects.create(
            mentor=self.mentor,
            title="How to get rich without getting lucky",
            youtube_video_id="dQw4w9WgXcQ",
        )
        self.chunk = ContentChunk.objects.create(
            video=self.video,
            chunk_index=0,
            text="Some chunk text",
        )

    def test_video_list_returns_status_field(self):
        response = self.client.get(reverse("videocontent-list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["status"], VideoContent.Status.NEW)

    def test_video_create_ignores_status_from_client(self):
        response = self.client.post(
            reverse("videocontent-list"),
            {
                "mentor": str(self.mentor.id),
                "title": "A valid title",
                "youtube_video_id": "xvFZjo5PgG0",
                "status": VideoContent.Status.READY,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = VideoContent.objects.get(id=response.data["id"])
        self.assertEqual(created.status, VideoContent.Status.NEW)

    def test_chunk_list_returns_video_relation(self):
        response = self.client.get(reverse("contentchunk-list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(str(response.data["results"][0]["video"]), str(self.video.id))
