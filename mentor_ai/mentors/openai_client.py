import os
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini")


def embed_query(text: str) -> list[float]:
    """
    Generate an embedding for the given text.
    :param text: The text to embed.
    :return: A list of floats representing the embedding.
    """
    if not text.strip():
        raise ValueError("text cannot be empty")
    
    resp = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return resp.data[0].embedding


def generate_answer(*, persona: str, user_text: str, context: str) -> str:
    """
    Generate an answer based on the given persona, user text, and context.
    :param persona: The persona prompt for the AI.
    :param user_text: The user's input text.
    :param context: The context snippets to inform the response.
    :return: The generated answer as a string.
    """
    if not all([persona.strip(), user_text.strip()]):
        raise ValueError("persona and user_text cannot be empty")
    
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": persona,
            },
            {
                "role": "user",
                "content": f"""User message:
{user_text}

Context snippets:
{context}
""",
            },
        ],
        temperature=0.7,
    )

    return resp.choices[0].message.content