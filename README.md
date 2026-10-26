# NoteSeek

A tiny semantic-notes API - save a note, search your notes by meaning (not keywords), get
LLM-generated tags. Built on [FastSpine](https://github.com/sleker78/fastspine) to demonstrate a
`VectorBaseService`/`LlmBaseService` pattern: two small `BaseService` mixins, each holding one
lazily-initialized client, combined via multiple inheritance into the service that actually does
the work.

This mirrors a real pattern (`VectorBase`/`LlmBase`) from a production FastSpine-based app, with
the proprietary backends (an internal gRPC vector DB + model gateway) swapped for public,
lightweight equivalents: **pgvector** (a Postgres extension, not a separate service) for vector
storage/search, and the public **OpenAI API** for embeddings + chat.

## You need an OpenAI API key

Unlike a pure-CRUD demo, this one calls a real LLM/embedding API - there's no local model, to keep
things light. Copy `.env.example` to `.env` and put a real key in it:

```bash
cp .env.example .env
# edit .env: OPENAI_API_KEY=sk-...
```

## Run it

```bash
make up
```

Then open **http://localhost:8001/docs** for the Swagger UI.

Other commands: `make logs`, `make restart`, `make reset` (wipe the DB), `make down`.

## Endpoints

| Method | Path | What it does |
|---|---|---|
| `POST` | `/notes` | Create a note - embedded (OpenAI) and stored (pgvector) |
| `GET` | `/notes` | List all notes |
| `GET` | `/notes/search?q=...&limit=5` | Semantic search - embeds the query, orders by cosine distance |
| `POST` | `/notes/{id}/tags` | Ask the LLM for 3-5 tags for this note, persists them |
| `DELETE` | `/notes/{id}` | Delete a note |

## CLI

The same `NoteService` the API uses, from the terminal:

```bash
make cli ARGS='create "Remember to water the plants on Fridays"'
make cli ARGS="list"
make cli ARGS='search "watering schedule"'
make cli ARGS="tags 1"
make cli ARGS="delete 1"
```

## The VectorBase / LlmBase pattern

```python
class VectorBaseService(BaseService):
    @property
    def embeddings_client(self) -> AsyncOpenAI: ...  # lazy
    async def embed_text(self, text: str) -> list[float]: ...
    @cache_method_async(expire=settings.EMBEDDING_CACHE_SECONDS)
    async def embed_text_cached(self, text: str) -> list[float]: ...

class LlmBaseService(BaseService):
    @property
    def llm_client(self) -> AsyncOpenAI: ...  # lazy

class NoteService(VectorBaseService, LlmBaseService):
    def __init__(self, db: NoteRepositoryManager):
        self.db = db
        VectorBaseService.__init__(self)
        LlmBaseService.__init__(self)
```

Neither mixin touches the database - `VectorBaseService` only knows how to turn text into a
vector; *where* that vector is stored/queried is `NoteRepository`'s job
(`Note.embedding.cosine_distance(...)`, via pgvector). `embed_text_cached` means re-embedding the
exact same text (e.g. a repeated search query) within `EMBEDDING_CACHE_SECONDS` is a Redis cache
hit, not a second OpenAI call.

`NoteService`'s constructor is the only one FastSpine's DI ever inspects - `VectorBaseService`/
`LlmBaseService.__init__` take no arguments, so they're called directly rather than through
`super()`, with no MRO ambiguity.

## Architecture

- `app/db/models.py` - `Note` (text, `pgvector`-backed `embedding` column, `tags`)
- `app/db/sessions.py` + `app/bootstrap.py` - the one `RepositoryManager` and its registration
- `app/repositories/note_repository.py` - `search_similar` (the one pgvector query)
- `app/services/vector_base.py`, `app/services/llm_base.py` - the two mixins
- `app/services/note_service.py` - combines both, holds the actual business logic
- `app/main.py` / `app/cli/main.py` - the 5 routes / 5 CLI commands, each one `NoteService` call

See also: [pollify](https://github.com/sleker78/pollify), a sibling demo with no vector/LLM
pieces, just the plain service-repository + caching pattern.

## Local dev without Docker

Needs a local Postgres (with the `vector` extension available) and Redis:

```bash
uv sync
uv run uvicorn app.main:app --reload
```
