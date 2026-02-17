# MentorAI Backend

Django + DRF backend for a mentor-persona chat system powered by RAG over YouTube transcripts.

## What This Project Does

- Manages mentors and their source videos.
- Extracts YouTube transcripts, chunks them, and stores embeddings in PostgreSQL (`pgvector`).
- Provides authenticated chat endpoint (`JWT`) that retrieves relevant chunks and generates answers with OpenAI.
- Runs transcript processing asynchronously with Celery workers.
- Exposes OpenAPI/Swagger docs via `drf-spectacular`.

## Tech Stack

- Python 3.11
- Django 5 + Django REST Framework
- PostgreSQL + `pgvector`
- Redis
- Celery + `django-celery-beat`
- OpenAI API
- `youtube-transcript-api`

## Project Structure

- `mentor_ai/mentor_ai/` - Django settings, URLs, Celery app
- `mentor_ai/mentor_knowledge/` - data models, transcript pipeline, ingestion API
- `mentor_ai/mentors/` - auth + chat API (JWT + RAG flow)
- `mentor_ai/docker-compose.yml` - app + db + redis + worker + beat

## Run The Project (Docker Required)

From repository root:

```powershell
cd mentor_ai
docker compose up --build
```

In another terminal:

```powershell
cd mentor_ai
docker compose run --rm app python manage.py migrate
docker compose run --rm app python manage.py createsuperuser
```

Server URL: `http://127.0.0.1:8000`

Docs:

- Swagger: `http://127.0.0.1:8000/api/docs/`
- ReDoc: `http://127.0.0.1:8000/api/redoc/`
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`

## Main API Endpoints

### Content Management (`mentor_knowledge`)

Base URL: `/`

- `GET/POST /mentors/`
- `GET/PATCH/DELETE /mentors/{id}/`
- `GET/POST /videos/`
- `GET/PATCH/DELETE /videos/{id}/`
- `POST /videos/{id}/enqueue-transcript/` - queue transcript + chunk + embedding pipeline
- `GET /videos/{id}/processing-status/` - current processing status
- `GET/POST /chunks/`
- `GET/PATCH/DELETE /chunks/{id}/`

### Auth + Chat (`mentors.api`)

Base URL: `/api/`

- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/refresh/`
- `POST /api/mentors/{mentor_slug}/chat/` (requires `Authorization: Bearer <access_token>`)

## Recommended Usage Flow

1. Create mentor (`POST /mentors/`).
2. Create video with YouTube ID (`POST /videos/`).
3. Queue transcript processing (`POST /videos/{id}/enqueue-transcript/`).
4. Poll status (`GET /videos/{id}/processing-status/`) until `ready`.
5. Register/login and call chat endpoint with `mentor_slug`.

## Data Model Overview

- `Mentor` - persona metadata (`name`, `slug`, `bio`, `primary_language`)
- `VideoContent` - mentor video with pipeline status:
  - `new`, `queued`, `fetched`, `chunked`, `embedded`, `ready`, `failed`
- `ContentChunk` - text chunk + timing + vector embedding (`VectorField(1536)`)

## Environment Variables

Core:

- `OPENAI_API_KEY` - required for embeddings/chat
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- `REDIS_URL` (default `redis://redis:6379`)
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` (defaults derived from `REDIS_URL`)

Embedding/Chunking:

- `EMBEDDING_MODEL` (default `text-embedding-3-small`)
- `EMBEDDING_DIMENSIONS` (default `1536`)
- `CHUNK_SIZE_WORDS` (default `350`)
- `CHUNK_OVERLAP_WORDS` (default `50`)

Chat model overrides:

- `OPENAI_EMBEDDING_MODEL` (default `text-embedding-3-small`)
- `OPENAI_CHAT_MODEL` (default `gpt-4o-mini`)

Optional YouTube proxy:

- `YOUTUBE_PROXY_USER`
- `YOUTUBE_PROXY_PASS`
- `YOUTUBE_PROXY_COUNTRIES` (comma-separated country codes)

Legacy/optional news ingestion settings still present in code:

- `NEWS_API_KEY`
- `NEWS_API_URL`
- `NEWS_API_QUERY`

## Useful Management Command

Process video manually:

```powershell
cd mentor_ai
docker compose run --rm app python manage.py process_video --video-id <uuid> --from-youtube
```

Or process all `new` videos:

```powershell
cd mentor_ai
docker compose run --rm app python manage.py process_video --process-all-new --from-youtube
```

## Run Tests

From `mentor_ai/`:

```powershell
cd mentor_ai
docker compose run --rm app python manage.py test
```
