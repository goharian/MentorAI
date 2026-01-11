from articles.models import Mentor
from mentors.openai_client import embed_query, generate_answer
from mentors.retrieval import retrieve_mentor_chunks
from mentors.prompts import build_persona_prompt


class MentorNotFoundError(Exception):
    """Raised when the requested mentor is not found in the system"""
    pass


def chat_with_mentor(
    *, 
    mentor_slug: str, 
    message: str, 
    top_k: int = 6,
    include_metadata: bool = True
) -> dict:
    """
    Main chat service function implementing RAG pipeline:
    1. Convert user message to embedding vector
    2. Retrieve top-k relevant transcript chunks for the mentor
    3. Generate answer using RAG with persona, user message, and context
    4. Return answer and retrieved chunks
    
    Args:
        mentor_slug (str): The slug identifier for the mentor
        message (str): The user's input message
        top_k (int, optional): Number of context chunks to retrieve. Defaults to 6
        include_metadata (bool, optional): Whether to include full metadata. Defaults to True
        
    Returns:
        dict: Dictionary containing the generated answer and retrieved context chunks
        
    Raises:
        MentorNotFoundError: If the mentor is not found in the database
        ValueError: If the message is empty or top_k is out of valid range
    """
    # Input validation
    if not message or not message.strip():
        raise ValueError("Message cannot be empty")
    
    if top_k < 1 or top_k > 12:
        raise ValueError("top_k must be between 1 and 12")

    # Retrieve mentor
    try:
        mentor = Mentor.objects.get(slug=mentor_slug)
    except Mentor.DoesNotExist:
        raise MentorNotFoundError(f"Mentor '{mentor_slug}' not found in the system")
    
    # Build persona prompt
    persona_prompt = build_persona_prompt(
        mentor_name=mentor.name,
        mentor_slug=mentor.slug,
        mentor_bio=mentor.bio,
    )
    
    # Convert question to embedding
    query_emb = embed_query(message)
    
    # Retrieve relevant chunks
    chunks = retrieve_mentor_chunks(
        mentor_slug=mentor_slug, 
        query_embedding=query_emb, 
        k=top_k
    )

    # Build context string
    context = _build_context_string(chunks) if chunks else "(no relevant context found)"

    # Generate answer
    answer = generate_answer(
        persona=persona_prompt,
        user_text=message,
        context=context,
    )

    # Build response
    response = {
        "answer": answer,
        "mentor_name": mentor.name,
        "chunks_found": len(chunks),
    }
    
    if include_metadata:
        response["retrieved"] = _format_retrieved_chunks(chunks)
    
    return response


def _build_context_string(chunks) -> str:
    """
    Build formatted context string from retrieved chunks
    
    Args:
        chunks: List of TranscriptChunk objects
        
    Returns:
        str: Formatted context string
    """
    return "\n\n".join(
        [
            (
                f"[{i+1}] {chunk.text}\n"
                f"(source: {chunk.video.title} | yt: {chunk.video.youtube_video_id} | "
                f"idx: {chunk.chunk_index} | {chunk.start_seconds}-{chunk.end_seconds}s)"
            )
            for i, chunk in enumerate(chunks)
        ]
    )


def _format_retrieved_chunks(chunks) -> list[dict]:
    """
    Format retrieved chunks into JSON-serializable structure
    
    Args:
        chunks: List of TranscriptChunk objects
        
    Returns:
        list[dict]: List of dictionaries with metadata for each chunk
    """
    return [
        {
            "chunk_id": str(c.id),
            "distance": float(getattr(c, "distance", 0.0)),
            "video_id": str(c.video_id),
            "video_title": c.video.title,
            "youtube_video_id": c.video.youtube_video_id,
            "chunk_index": c.chunk_index,
            "start_seconds": c.start_seconds,
            "end_seconds": c.end_seconds,
            "text": c.text[:200] + "..." if len(c.text) > 200 else c.text,  # Truncate long text
        }
        for c in chunks
    ]