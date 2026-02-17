from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from .models import Mentor, VideoContent, ContentChunk
from .serializers import MentorSerializer, VideoContentSerializer, ContentChunkSerializer
from .tasks import process_video_transcript_task


class MentorViewSet(ModelViewSet):
    queryset = Mentor.objects.all()
    serializer_class = MentorSerializer


class VideoContentViewSet(ModelViewSet):
    queryset = VideoContent.objects.select_related("mentor").order_by("id")
    serializer_class = VideoContentSerializer

    @action(detail=True, methods=["post"], url_path="enqueue-transcript")
    def enqueue_transcript(self, request, pk=None):
        video = self.get_object()
        processing_states = {
            VideoContent.Status.QUEUED,
            VideoContent.Status.FETCHED,
            VideoContent.Status.CHUNKED,
            VideoContent.Status.EMBEDDED,
        }

        updated = (
            VideoContent.objects
            .filter(id=video.id)
            .exclude(status__in=processing_states)
            .update(status=VideoContent.Status.QUEUED)
        )
        if updated == 0:
            video.refresh_from_db(fields=["status"])
            return Response(
                {
                    "video_id": str(video.id),
                    "status": video.status,
                    "detail": "Video is already being processed.",
                },
                status=status.HTTP_409_CONFLICT,
            )

        video.status = VideoContent.Status.QUEUED

        try:
            task = process_video_transcript_task.delay(str(video.id))
        except Exception:
            VideoContent.objects.filter(id=video.id).update(status=VideoContent.Status.FAILED)
            return Response(
                {
                    "video_id": str(video.id),
                    "status": VideoContent.Status.FAILED,
                    "detail": "Failed to queue transcript processing task.",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(
            {
                "video_id": str(video.id),
                "status": video.status,
                "task_id": task.id,
                "detail": "Transcript processing queued.",
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["get"], url_path="processing-status")
    def processing_status(self, request, pk=None):
        video = self.get_object()
        return Response(
            {
                "video_id": str(video.id),
                "status": video.status,
            },
            status=status.HTTP_200_OK,
        )


class ContentChunkViewSet(ModelViewSet):
    queryset = ContentChunk.objects.select_related("video", "video__mentor").order_by("video_id", "chunk_index", "id")
    serializer_class = ContentChunkSerializer
