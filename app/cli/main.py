"""NoteSeek CLI - the same NoteService the API uses, called from the terminal instead of HTTP."""

import typer

import app.bootstrap  # noqa: F401  (must run before any command uses NoteRepositoryManager)

from fastspine import load_service
from fastspine.cli.scoped_typer import ScopedTyper

from app.services.note_service import NoteNotFoundError, NoteService

app = ScopedTyper(no_args_is_help=True, help="Manage NoteSeek notes from the terminal.")


@app.command("create", help="Create a note (embedded and stored).")
async def create_note(text: str):
    service = load_service(NoteService)
    note = await service.create_note(text)
    typer.echo(f"Created note #{note.id}: {note.text}")


@app.command("list", help="List all notes.")
async def list_notes():
    service = load_service(NoteService)
    notes = await service.list_notes()
    if not notes:
        typer.echo("No notes yet - create one with `create`.")
        return
    for note in notes:
        tags = f" [{', '.join(note.tags)}]" if note.tags else ""
        typer.echo(f"[{note.id}] {note.text}{tags}")


@app.command("search", help="Semantic search across notes.")
async def search(query: str, limit: int = 5):
    service = load_service(NoteService)
    notes = await service.search(query, limit)
    if not notes:
        typer.echo("No matches.")
        return
    for note in notes:
        typer.echo(f"[{note.id}] {note.text}")


@app.command("tags", help="Generate tags for a note via the LLM.")
async def tags(note_id: int):
    service = load_service(NoteService)
    try:
        result = await service.generate_tags(note_id)
    except NoteNotFoundError as err:
        typer.echo(str(err), err=True)
        raise typer.Exit(code=1) from err
    typer.echo(", ".join(result))


@app.command("delete", help="Delete a note.")
async def delete(note_id: int):
    service = load_service(NoteService)
    try:
        await service.delete_note(note_id)
    except NoteNotFoundError as err:
        typer.echo(str(err), err=True)
        raise typer.Exit(code=1) from err
    typer.echo("Deleted.")


if __name__ == "__main__":
    app()
