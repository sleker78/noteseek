from sqlalchemy.ext.asyncio import AsyncSession

from fastspine import RepositoryManager


class NoteRepositoryManager(RepositoryManager[AsyncSession]):
    """Repository manager for the NoteSeek database."""
