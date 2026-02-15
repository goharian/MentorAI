from django.db import transaction
from typing import Dict, List

from articles.chunking_service import TranscriptChunker
from articles.embedding_service import EmbeddingService
from articles.models import ContentChunk, VideoContent
from .youtube_transcript import get_transcript


class VideoProcessingService:
    """
    Service for processing video transcripts into chunked embeddings.
    This service uses TranscriptChunker to split transcripts into chunks
    """

    def __init__(self, mock_embeddings=False):
        self.mock_embeddings = mock_embeddings
        self.chunker = TranscriptChunker()
        self.embedding_service = EmbeddingService()

    def process_video_with_transcript(
        self, 
        video: VideoContent, 
        transcript: List[Dict]
    ) -> dict:
        
        try:
            # Re-processing should replace previous chunks rather than failing on unique constraints.
            video.chunks.all().delete()

            # Chunking
            video.status = VideoContent.Status.CHUNKED
            video.save()
            
            chunks_data = self.chunker.chunk_transcript(transcript)
            if not chunks_data:
                raise ValueError("No chunks were created from the transcript.")
            
            # Embedding
            video.status = VideoContent.Status.EMBEDDED
            video.save()
            self._create_chunks_with_embeddings(video, chunks_data)

            # Finalize
            video.status = VideoContent.Status.READY
            video.save()

            return {
                'success': True,
                'chunks_created': len(chunks_data),
                'total_duration': chunks_data[-1].end_seconds if chunks_data else 0
            }
        
        except Exception as e:
            video.status = VideoContent.Status.FAILED
            video.save()
            raise Exception(f"Video processing failed: {str(e)}")

    def process_video_from_youtube(self, video: VideoContent) -> dict:
        """
        Fetch transcript from YouTube and process the video end-to-end.
        """
        transcript_result = get_transcript(video.youtube_video_id)
        if not transcript_result.get("success"):
            raise ValueError(
                f"Transcript fetch failed for video {video.youtube_video_id}: "
                f"{transcript_result.get('error', 'Unknown error')}"
            )

        video.status = VideoContent.Status.FETCHED
        video.save(update_fields=["status", "updated_at"])

        transcript_entries = transcript_result.get("entries", [])
        if not transcript_entries:
            raise ValueError("Transcript is empty")

        result = self.process_video_with_transcript(video, transcript_entries)
        return {
            **result,
            "transcript_entries": transcript_result.get("entries_count", 0),
        }
        
    @transaction.atomic
    def _create_chunks_with_embeddings(self, video: VideoContent, chunks_data: List):
        """
        Create video chunks and their embeddings in the database.

        Args:
            video (VideoContent): The video content object.
            chunks_data (List): List of chunk data with text and metadata.
        """
        # Generate embeddings for all chunks
        texts = [chunk.text for chunk in chunks_data]
        embeddings = self.embedding_service.generate_embeddings_batch(texts)

        # Create ContentChunk objects
        chunks_to_create = []
        for chunk_data, embedding in zip(chunks_data, embeddings):
            chunk = ContentChunk(
                video=video,
                chunk_index=chunk_data.chunk_index,
                text=chunk_data.text,
                start_seconds=int(chunk_data.start_seconds),
                end_seconds=int(chunk_data.end_seconds),
                embedding=embedding
            )
            chunks_to_create.append(chunk)

        # Bulk create chunks in the database
        ContentChunk.objects.bulk_create(chunks_to_create)
