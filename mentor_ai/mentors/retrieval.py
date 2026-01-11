from pgvector.django import CosineDistance
from articles.models import ContentChunk


def retrieve_mentor_chunks(*, mentor_slug: str, query_embedding: list[float], k: int = 6):
    """
    Vector search over ContentChunk.embedding, scoped to a mentor via joins:
    ContentChunk -> VideoContent -> Mentor
    1. Filter ContentChunks to those belonging to the specified mentor and having non-null embeddings.
    2. Annotate each ContentChunk with its cosine distance to the query_embedding.
    3. Order by distance and return the top k closest chunks.
    4. Return the results as a list.
    Args:
        mentor_slug (str): The slug identifier for the mentor.
        query_embedding (list[float]): The embedding vector to search against.
        k (int, optional): The number of top results to return. Defaults to 6.
    Returns:
        list[ContentChunk]: The top k closest ContentChunks to the query_embedding for the specified mentor.
    """
    qs = (
        ContentChunk.objects
        .filter(video__mentor__slug=mentor_slug, embedding__isnull=False)
        .select_related("video", "video__mentor")
        .annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by("distance")[:k]
    )
    return list(qs)
