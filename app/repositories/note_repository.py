from sqlalchemy import select

from fastspine import BaseRepository

from app.db.models import Note


class NoteRepository(BaseRepository[Note]):
    """Repository for `Note` rows."""

    async def search_similar(self, embedding: list[float], limit: int = 5) -> list[Note]:
        """Return notes ordered by cosine distance to the given embedding (closest first)."""
        stmt = select(Note).order_by(Note.embedding.cosine_distance(embedding)).limit(limit)
        return list((await self.db.execute(stmt)).scalars().all())
