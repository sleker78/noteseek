from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, String
from sqlalchemy.orm import Mapped, mapped_column

from fastspine.mixins import CreatedAtMixin
from fastspine.models.base import Base

from app.settings import settings


class Note(Base, CreatedAtMixin):
    __tablename__ = "notes"

    text: Mapped[str]
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.EMBEDDING_DIM))
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
