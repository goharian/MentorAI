import logging
import time
from django.db import transaction
from typing import Dict, List

from mentor_knowledge.chunking_service import TranscriptChunker
from mentor_knowledge.embedding_service import EmbeddingService
from mentor_knowledge.models import ContentChunk, VideoContent
from .youtube_transcript import get_transcript

logger = logging.getLogger(__name__)


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
        total_start = time.perf_counter()

        try:
            # Re-processing should replace previous chunks rather than failing on unique constraints.
            video.chunks.all().delete()

            # Chunking
            video.status = VideoContent.Status.CHUNKED
            video.save()

            chunking_start = time.perf_counter()
            chunks_data = self.chunker.chunk_transcript(transcript)
            if not chunks_data:
                raise ValueError("No chunks were created from the transcript.")
            logger.info(
                "Chunking completed | video_id=%s chunks=%s duration_sec=%.2f",
                video.id,
                len(chunks_data),
                time.perf_counter() - chunking_start,
            )
            
            # Embedding
            video.status = VideoContent.Status.EMBEDDED
            video.save()
            embedding_start = time.perf_counter()
            self._create_chunks_with_embeddings(video, chunks_data)
            logger.info(
                "Embedding completed | video_id=%s chunks=%s duration_sec=%.2f",
                video.id,
                len(chunks_data),
                time.perf_counter() - embedding_start,
            )

            # Finalize
            video.status = VideoContent.Status.READY
            video.save()
            total_duration = time.perf_counter() - total_start
            logger.info(
                "Video processing finished | video_id=%s total_duration_sec=%.2f",
                video.id,
                total_duration,
            )

            return {
                'success': True,
                'chunks_created': len(chunks_data),
                'total_duration': chunks_data[-1].end_seconds if chunks_data else 0
            }
        
        except Exception as e:
            video.status = VideoContent.Status.FAILED
            video.save()
            logger.exception("Video processing failed | video_id=%s", video.id)
            raise Exception(f"Video processing failed: {str(e)}")

    def process_video_from_youtube(self, video: VideoContent) -> dict:
        """
        Fetch transcript from YouTube and process the video end-to-end.
        """
        logger.info("Fetching transcript | video_id=%s youtube_video_id=%s", video.id, video.youtube_video_id)
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
        logger.info(
            "Transcript fetched | video_id=%s entries=%s",
            video.id,
            transcript_result.get("entries_count", 0),
        )

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

