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

## Basic AWS Deployment (EC2 + Docker Compose)

This is the fastest production-like setup for this repo.

### 1. Create an EC2 instance

- Ubuntu 22.04 (or 24.04)
- Open inbound ports in Security Group:
  - `22` (SSH) from your IP
  - `80` (HTTP) from internet

### 2. Install Docker on EC2

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin git
sudo usermod -aG docker $USER
newgrp docker
```

### 3. Pull project and configure env

```bash
git clone <your-repo-url>
cd MentorAI/mentor_ai
cp .env.example .env
```

Edit `.env` and set at least:

- `SECRET_KEY` (random strong value)
- `ALLOWED_HOSTS` (EC2 public IP or domain)
- `CSRF_TRUSTED_ORIGINS` (`http://<EC2_PUBLIC_IP>` or your HTTPS domain)
- `OPENAI_API_KEY`
- `DB_PASSWORD` (change from default)

### 4. Start services

```bash
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

### 5. Verify deployment

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f app
```

App URL:

- `http://<EC2_PUBLIC_IP>/api/docs/`

Optional admin user:

```bash
docker compose -f docker-compose.prod.yml exec app python manage.py createsuperuser
```

### 6. Update on new code

```bash
git pull
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```
