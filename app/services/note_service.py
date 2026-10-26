from app.db.models import Note
from app.db.sessions import NoteRepositoryManager
from app.repositories.note_repository import NoteRepository
from app.services.llm_base import LlmBaseService
from app.services.vector_base import VectorBaseService
from app.settings import settings


class NoteNotFoundError(Exception):
    pass


class NoteService(VectorBaseService, LlmBaseService):
    """Notes CRUD + semantic search (VectorBaseService) + LLM tagging (LlmBaseService)."""

    def __init__(self, db: NoteRepositoryManager):
        self.db = db
        VectorBaseService.__init__(self)
        LlmBaseService.__init__(self)

    async def create_note(self, text: str) -> Note:
        embedding = await self.embed_text_cached(text)
        note = Note(text=text, embedding=embedding, tags=[])
        return await self.db.get(NoteRepository).create(note, commit=True)

    async def list_notes(self) -> list[Note]:
        return await self.db.get(NoteRepository).filter_by()

    async def search(self, query: str, limit: int = 5) -> list[Note]:
        embedding = await self.embed_text_cached(query)
        return await self.db.get(NoteRepository).search_similar(embedding, limit)

    async def generate_tags(self, note_id: int) -> list[str]:
        note = await self._get_note_or_raise(note_id)
        response = await self.llm_client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": f"Give 3-5 short, lowercase, comma-separated tags for this note:\n\n{note.text}",
                }
            ],
        )
        content = response.choices[0].message.content or ""
        tags = [tag.strip() for tag in content.split(",") if tag.strip()]
        note.tags = tags
        await self.db.commit()
        return tags

    async def delete_note(self, note_id: int) -> None:
        note = await self._get_note_or_raise(note_id)
        await self.db.get(NoteRepository).delete(note, commit=True)

    async def _get_note_or_raise(self, note_id: int) -> Note:
        note = await self.db.get(NoteRepository).get_by_id(note_id)
        if note is None:
            raise NoteNotFoundError(f"Note {note_id} not found")
        return note
