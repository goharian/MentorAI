"""
Serializers for the Mentor AI application models.
"""
from rest_framework import serializers
from .models import Mentor, VideoContent, ContentChunk


class MentorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mentor
        fields = ["id", "name", "slug", "created_at", "updated_at"]


class VideoContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoContent
        fields = [
            "id", "mentor", "title", "youtube_video_id", "created_at", "updated_at",
        ]


class ContentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentChunk
        fields = ["id", "video", "chunk_index", "text", "created_at"]
