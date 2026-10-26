from contextlib import asynccontextmanager
from typing import Annotated

import app.bootstrap  # noqa: F401  (must run before any route uses NoteRepositoryManager)

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text

from fastspine import FastSpineApp, service_dep
from fastspine.models.base import Base

from app.schemas import NoteCreateRequest, NoteResponse
from app.services.note_service import NoteNotFoundError, NoteService
from app.settings import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    engine = settings.db_config.create_async_engine()
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    yield


app = FastSpineApp(settings=settings, lifespan=lifespan)

NoteServiceDep = Annotated[NoteService, Depends(service_dep(NoteService))]


@app.post("/notes", response_model=NoteResponse)
async def create_note(payload: NoteCreateRequest, service: NoteServiceDep):
    note = await service.create_note(payload.text)
    return NoteResponse.model_validate(note)


@app.get("/notes", response_model=list[NoteResponse])
async def list_notes(service: NoteServiceDep):
    notes = await service.list_notes()
    return [NoteResponse.model_validate(note) for note in notes]


@app.get("/notes/search", response_model=list[NoteResponse])
async def search_notes(q: str, service: NoteServiceDep, limit: int = 5):
    notes = await service.search(q, limit)
    return [NoteResponse.model_validate(note) for note in notes]


@app.post("/notes/{note_id}/tags", response_model=list[str])
async def generate_tags(note_id: int, service: NoteServiceDep):
    try:
        return await service.generate_tags(note_id)
    except NoteNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err


@app.delete("/notes/{note_id}", status_code=204)
async def delete_note(note_id: int, service: NoteServiceDep):
    try:
        await service.delete_note(note_id)
    except NoteNotFoundError as err:
        raise HTTPException(status_code=404, detail=str(err)) from err
