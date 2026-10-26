from openai import AsyncOpenAI

from fastspine import BaseService
from fastspine.cache.cache_decorater import cache_method_async

from app.settings import settings


class VectorBaseService(BaseService):
    """Base class for embedding generation.

    Mirrors finder2's `VectorBase` pattern (lazy client property via `openai.AsyncOpenAI`
    instead of the proprietary Specter/Qdrant stack) - subclasses get `embed_text`/
    `embed_text_cached` for free; where the resulting embedding gets stored/queried
    (here: pgvector, via `NoteRepository`) is a separate concern.
    """

    def __init__(self):
        self._embeddings_client: AsyncOpenAI | None = None

    @property
    def embeddings_client(self) -> AsyncOpenAI:
        """Lazy initialization of the embeddings client."""
        if self._embeddings_client is None:
            self._embeddings_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._embeddings_client

    async def embed_text(self, text: str) -> list[float]:
        """Embed text using the configured embedding model."""
        response = await self.embeddings_client.embeddings.create(model=settings.EMBEDDING_MODEL, input=text)
        return response.data[0].embedding

    @cache_method_async(expire=settings.EMBEDDING_CACHE_SECONDS)
    async def embed_text_cached(self, text: str) -> list[float]:
        """Embed text, caching the result so re-embedding identical text is a cache hit."""
        return await self.embed_text(text)
