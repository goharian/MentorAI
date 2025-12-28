from rest_framework.viewsets import ModelViewSet
from .models import Mentor, VideoContent, ContentChunk
from .serializers import MentorSerializer, VideoContentSerializer, ContentChunkSerializer


class MentorViewSet(ModelViewSet):
    queryset = Mentor.objects.all()
    serializer_class = MentorSerializer


class VideoContentViewSet(ModelViewSet):
    queryset = VideoContent.objects.select_related("mentor").all()
    serializer_class = VideoContentSerializer


class ContentChunkViewSet(ModelViewSet):
    queryset = ContentChunk.objects.select_related("video", "video__mentor").all()
    serializer_class = ContentChunkSerializer
