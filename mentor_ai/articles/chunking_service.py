"""
Docstring for mentor_ai.articles.chunking_service
"""

from typing import List, Dict
from dataclasses import dataclass

@dataclass
class ChunkData:
    """Data structure for a content chunk."""
    text: str
    chunk_index: int
    start_seconds: float
    end_seconds: float
    word_count: int

class TranscriptChunker:
    """Service for chunking video transcripts into smaller segments."""

    def __init__(self, chunk_size_words: int = 350, overlap_words: int = 50):
        """
        Initialize the TranscriptChunker with specified chunk size and overlap.
        Args:
            chunk_size_words (int): Number of words per chunk.
            overlap_words (int): Number of overlapping words between chunks.
        """
        self.chunk_size = chunk_size_words
        self.overlap = overlap_words

    def chunk_transcript(self, transcript: List[Dict]) -> List[ChunkData]:
        """
        Chunk the given transcript into smaller segments.
        Args:
            transcript (List[Dict]): List of transcript segments with 'text', 'start', and 'end' keys.
        Returns:
            List[ChunkData]: List of chunked data.
        """
        if not transcript:
            return []
        
        words_with_time = self._build_words_timeline(transcript)
        if not words_with_time:
            return []
        
        chunks = []
        chunk_index = 0
        start_idx = 0

        while start_idx < len(words_with_time):
            end_idx = min(start_idx + self.chunk_size, len(words_with_time))
            chunk_words = words_with_time[start_idx:end_idx]
            text = ' '.join([w['word'] for w in chunk_words])
            start_seconds = chunk_words[0]['start']
            end_seconds = chunk_words[-1]['end']

            chunk_data = ChunkData(
                text=text,
                chunk_index=chunk_index,
                start_seconds=round(start_seconds, 2),
                end_seconds=round(end_seconds, 2),
                word_count=len(chunk_words)
            )

            chunks.append(chunk_data)
            start_idx = end_idx - self.overlap
            chunk_index += 1

            if start_idx >= len(words_with_time) - self.overlap:
                break

        return chunks
    
    def _build_words_timeline(self, transcript: List[Dict]) -> List[Dict]:
        """
        Build a timeline of words with their start and end times from the transcript.
        Args:
            transcript (List[Dict]): List of transcript segments.
        Returns:
            List[Dict]: List of words with their timing information.
        """
        words_timeline = []

        for segment in transcript:
            text = segment.get('text', '').strip()
            start = segment.get('start', 0.0)
            duration = segment.get('duration', 0.0)
            end = start + duration
            
            if not text:
                continue

            segment_words = text.split()
            if not segment_words:
                continue

            avg_word_duration = duration / len(segment_words) if len(segment_words) > 0 else 0

            for i, word in enumerate(segment_words):
                word_start = start + (i * avg_word_duration)
                word_end = word_start + avg_word_duration
                
                words_timeline.append({
                    'word': word,
                    'start': word_start,
                    'end': word_end
                })
        
        return words_timeline