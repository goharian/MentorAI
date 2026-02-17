from unittest import mock

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from mentor_knowledge.models import Mentor, VideoContent


class VideoProcessingApiTests(APITestCase):
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

    @mock.patch("mentor_knowledge.views.process_video_transcript_task.delay")
    def test_enqueue_transcript_queues_celery_task(self, mock_delay):
        mock_delay.return_value.id = "task-123"

        response = self.client.post(
            reverse("videocontent-enqueue-transcript", kwargs={"pk": self.video.pk}),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["task_id"], "task-123")

        self.video.refresh_from_db()
        self.assertEqual(self.video.status, VideoContent.Status.QUEUED)
        mock_delay.assert_called_once_with(str(self.video.id))

    @mock.patch("mentor_knowledge.views.process_video_transcript_task.delay")
    def test_enqueue_transcript_rejects_when_already_processing(self, mock_delay):
        self.video.status = VideoContent.Status.QUEUED
        self.video.save(update_fields=["status", "updated_at"])

        response = self.client.post(
            reverse("videocontent-enqueue-transcript", kwargs={"pk": self.video.pk}),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        mock_delay.assert_not_called()

    @mock.patch("mentor_knowledge.views.process_video_transcript_task.delay", side_effect=RuntimeError("broker down"))
    def test_enqueue_transcript_returns_503_when_queue_fails(self, _mock_delay):
        response = self.client.post(
            reverse("videocontent-enqueue-transcript", kwargs={"pk": self.video.pk}),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.video.refresh_from_db()
        self.assertEqual(self.video.status, VideoContent.Status.FAILED)

    def test_processing_status_returns_video_status(self):
        self.video.status = VideoContent.Status.FETCHED
        self.video.save(update_fields=["status", "updated_at"])

        response = self.client.get(
            reverse("videocontent-processing-status", kwargs={"pk": self.video.pk}),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], VideoContent.Status.FETCHED)

