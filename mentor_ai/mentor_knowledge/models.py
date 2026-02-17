"""
Mentor model for storing mentorship information.
"""
import uuid
from django.db import models
from django.core.validators import MinLengthValidator
from pgvector.django import VectorField


class Mentor(models.Model):
    """Mentor object."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, 
                            verbose_name="Mentor name",
                            null=False,
                            help_text="Name shown to users. Should match the real public figure.")
    slug = models.SlugField(max_length=200, unique=True, 
                            help_text="Unique identifier for the mentor, used in URLs.")
    primary_language = models.CharField(max_length=50, default="en")
    bio = models.TextField(blank=True, null=True, 
                           help_text="Short biography of the mentor.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
    

class VideoContent(models.Model):
    """Video content object."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE, related_name="videos")
    title = models.CharField(max_length=512,
                             validators=[MinLengthValidator(5, "Title must be at least 5 characters long.")])
    youtube_video_id = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Status(models.TextChoices):
        NEW = "new", "New"
        QUEUED = "queued", "Queued"
        FETCHED = "fetched", "Transcript fetched"
        CHUNKED = "chunked", "Chunked"
        EMBEDDED = "embedded", "Embedded"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW
    )


    class Meta:
        unique_together = [("mentor", "youtube_video_id")]
        indexes = [
            models.Index(fields=["mentor", "youtube_video_id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.title} by {self.mentor.name}"
    

class ContentChunk(models.Model):
    """Content chunk object."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.ForeignKey(VideoContent, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.PositiveIntegerField() 
    text = models.TextField()
    start_seconds = models.IntegerField(null=True, blank=True)
    end_seconds = models.IntegerField(null=True, blank=True)
    embedding = VectorField(dimensions=1536, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("video", "chunk_index")]
        indexes = [
            models.Index(fields=["video", "chunk_index"]),
        ]

    def __str__(self) -> str:
        return f"{self.video.youtube_video_id} #{self.chunk_index}"
