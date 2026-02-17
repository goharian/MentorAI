from openai import OpenAI
from django.conf import settings
from typing import List

class EmbeddingService:
    """Service for generating embeddings using OpenAI."""

    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EMBEDDING_MODEL

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for the given text.
        Args:
            text (str): The text to generate embeddings for.    
        Returns:
            List[float]: The embedding for the given text.
        """
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"Failed to create embedding: {str(e)}")
        
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        Args:
            texts (List[str]): The list of texts to generate embeddings for.
        Returns:
            List[List[float]]: The embeddings for each text.
        """
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            # Sort embeddings by index, as OpenAI may return them out of order
            sorted_embeddings = sorted(response.data, key=lambda x: x.index)
            return [item.embedding for item in sorted_embeddings]
        except Exception as e:
            raise Exception(f"Failed to create embeddings: {str(e)}")