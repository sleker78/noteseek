from openai import AsyncOpenAI

from fastspine import BaseService

from app.settings import settings


class LlmBaseService(BaseService):
    """Base class for LLM operations.

    Mirrors finder2's `LlmBase` pattern exactly (lazy `AsyncOpenAI` client property) - there,
    it's pointed at MDPI's internal gateway with session-based auth; here, at the public OpenAI
    API with a plain API key. Subclasses use `self.llm_client` directly for whatever call they need.
    """

    def __init__(self):
        self._llm_client: AsyncOpenAI | None = None

    @property
    def llm_client(self) -> AsyncOpenAI:
        """Lazy initialization of the LLM client."""
        if self._llm_client is None:
            self._llm_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._llm_client
