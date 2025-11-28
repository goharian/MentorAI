
# news-summarization-service

A small Django service that fetches news articles, stores them, and provides summaries using OpenAI (ChatGPT). The project includes an `articles` app with endpoints to list articles, view article details, and request a generated summary (with caching).

**Quick links**
- Project: `news-summarization-service`
- App: `news_summarizer/articles`

**Features**
- Fetch articles from the News API and store them in the database (`management` command `fetch_articles`).
- Summarize articles using OpenAI; summaries are cached in Redis to avoid repeated calls.
- REST API endpoints (DRF) to list articles, view details, and get article summaries.

**Contents**
- `news_summarizer/` — Django project settings and root files.
- `news_summarizer/articles/` — main app with models, views, services, and tests.

**Requirements**
- Python 3.11+ (project used with a virtualenv in development)
- PostgreSQL (used in Docker compose), or change `DATABASES` in `news_summarizer/settings.py` for local sqlite usage
- Redis (caching)
- Docker & Docker Compose (optional, recommended for local full-stack run)
 - Celery & `django-celery-beat` (background task queue and periodic tasks)

**Detailed Setup**

**Prerequisites:**
- **Python:** `3.11+` installed and available on `PATH`.
- **Pip:** `pip` available (bundled with recent Python installs).
- **Docker (optional):** Docker Desktop for running the full stack (`Postgres` + `Redis`).

**Local development (recommended - venv)**

1. **Create a virtual environment** (PowerShell):

```powershell
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
```

2. **Install dependencies**:

```powershell
pip install -r news_summarizer/requirements.txt
```

3. **Configuration options**
- Use environment variables or a `.env` file loader (not included by default). The app looks for these vars at runtime:
	- `OPENAI_API_KEY` — (optional) OpenAI key to enable real summarization. If not set, the app uses a deterministic mock summary.
	- `NEWS_API_KEY` — (optional for fetch) API key used by the `fetch_articles` command.
	- DB/Redis connection variables are controlled via `news_summarizer/settings.py` when using Docker Compose. For quick local work you can switch to SQLite (see note below).

Example PowerShell session to set env vars for the current session:

```powershell
$env:OPENAI_API_KEY = 'sk-...'
$env:NEWS_API_KEY = 'newsapi-...'
```

4. **Apply database migrations**:

```powershell
python news_summarizer/manage.py migrate
```

5. **Create a superuser (optional)**:

```powershell
python news_summarizer/manage.py createsuperuser
```

6. **Run the development server**:

```powershell
python news_summarizer/manage.py runserver
```

Open `http://127.0.0.1:8000/` and use the API endpoints described below.

**Quick SQLite alternative**
- If you prefer not to run Postgres during development, edit `news_summarizer/settings.py` and replace the `DATABASES` block with:

```python
DATABASES = {
		'default': {
				'ENGINE': 'django.db.backends.sqlite3',
				'NAME': BASE_DIR / 'db.sqlite3',
		}
}
```

Then re-run `migrate` as above.

**Docker Compose (full stack: app, Postgres, Redis)**

From the project root run:

```powershell
cd news_summarizer
docker compose up --build
```

Notes:
- The compose stack provisions a Postgres DB and Redis per `docker-compose.yml`.
- To run management commands inside the container (example: migrate, createsuperuser, tests):

```powershell
docker compose run --rm app python manage.py migrate
docker compose run --rm app python manage.py createsuperuser
docker compose run --rm app python manage.py test
```

Background processing (Celery)
 - This project uses Celery for background processing and `django-celery-beat` for periodic jobs. The provided `docker-compose.yml` defines two additional services: `worker` (Celery worker) and `beat` (Celery beat scheduler).
 - Running `docker compose up --build` from the `news_summarizer` folder will start the `app`, `db`, `redis`, **and** the Celery `worker` and `beat` services so background tasks (queued by `fetch_articles`) are processed automatically.

Run Celery locally (venv)
 - If you're not using Docker for workers, start Redis (locally or via Docker) and then run these commands from the project root inside your activated venv:

```powershell
# Start a local Redis container (if you don't have Redis installed locally)
docker run --rm -p 6379:6379 redis:alpine

# In a separate shell (venv active) run the Celery worker:
celery -A news_summarizer worker -l info

# Optionally run Celery Beat for periodic tasks (uses django-celery-beat scheduler):
celery -A news_summarizer beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

**Fetching articles**
- The repository includes a management command to fetch articles from the News API:

```powershell
python news_summarizer/manage.py fetch_articles
```

The command fetches articles and queues them for background processing by Celery using articles.services.fetch_and_store_articles.

- You should set `NEWS_API_KEY` in your environment for the command to fetch real data. When running in Docker Compose you can pass the key into the container environment or use a compose override.

**Running tests**
- Locally (venv):

```powershell
& .\.venv\Scripts\Activate.ps1
python news_summarizer/manage.py test articles
```

- In Docker (recommended for consistency):

```powershell
cd news_summarizer
docker compose run --rm app python manage.py test articles
```

Notes about tests:
- Tests mock external services (OpenAI, network requests) and use Django's test DB. Caches are overridden to `LocMemCache` during tests so Redis isn't required.

**Environment variables**
- `OPENAI_API_KEY` — required to enable real OpenAI summarization. When missing, the app falls back to a mock summary.
- `NEWS_API_KEY` — API key for the News API used by the `fetch_articles` command.

**Setup — local (venv)**
1. Create and activate a virtual environment (PowerShell):
```powershell
python -m venv venv
& .\venv\Scripts\Activate.ps1
```
2. Install dependencies:
```powershell
pip install -r news_summarizer/requirements.txt
```
3. Configure environment variables. On Windows PowerShell you can set them for the session like:
```powershell
$env:OPENAI_API_KEY = 'sk-...'
$env:NEWS_API_KEY = 'newsapi-...'
```
4. Apply migrations:
```powershell
python news_summarizer/manage.py migrate
```
5. (Optional) Create a superuser:
```powershell
python news_summarizer/manage.py createsuperuser
```

**Run the development server**
```powershell
python news_summarizer/manage.py runserver
```

Then open `http://127.0.0.1:8000/`.

API endpoints (registered in `news_summarizer/articles/urls.py`):
- `GET /articles/` — paginated list of articles.
- `GET /articles/{id}/` — article details.
- `GET /articles/{id}/summary` — returns generated summary and `cached` flag.

Example (curl):
```powershell
curl http://127.0.0.1:8000/articles/1/summary
```

**Run with Docker Compose (recommended for matching production-like services)**
The repository includes a `Dockerfile` and `docker-compose.yml` under the `news_summarizer/` folder. Using Docker will bring up the app, Postgres, and Redis (as configured in `settings.py`).

From the project root run:
```powershell
cd news_summarizer
docker-compose up --build
```

To run management commands inside the container (e.g., migrate or tests):
```powershell
docker-compose run --rm app python manage.py migrate
docker-compose run --rm app python manage.py createsuperuser
docker-compose run --rm app python manage.py test
```

**Tests**
- Unit tests for the `articles` app are located in `news_summarizer/articles/tests.py`.
- The tests mock external services (OpenAI, requests) and use Django's test database.

Run tests locally (venv):
```powershell
& .\venv\Scripts\Activate.ps1
python news_summarizer/manage.py test articles
```

Or run tests inside Docker (recommended if you're using the project compose stack):
```powershell
cd news_summarizer
docker-compose run --rm app python manage.py test articles
```

Notes about tests and services:
- The project settings expect Redis for caching (cache alias `summaries`). When running tests, unit tests override caches to use Django's `LocMemCache` so Redis is not required for the test suite.
- If `OPENAI_API_KEY` is not set, the summarizer falls back to a deterministic mock summary to avoid external API calls.

**Management commands**
- `python news_summarizer/manage.py fetch_articles` — Fetches new articles from the News API and stores them in the database. The command uses `articles.services.fetch_and_store_articles`.

**Troubleshooting**
- If migrations fail because of database connectivity, either run the full stack with Docker Compose (it provides the `db` service) or update `news_summarizer/settings.py` to use a local sqlite DB for development:
  - Example change for quick local work:
	```python
	DATABASES = {
		'default': {
			'ENGINE': 'django.db.backends.sqlite3',
			'NAME': BASE_DIR / 'db.sqlite3',
		}
	}
	```
- If you see the message from `settings.py` about `OPENAI_API_KEY` not being defined, it's informational — either set `OPENAI_API_KEY` to enable real summarization or ignore it and use the mock fallback.

**CI / Recommendations**
- Add a GitHub Actions workflow that runs `pip install -r requirements.txt` and `python manage.py test` inside a matrix that uses SQLite or a docker-compose service set (Postgres+Redis) depending on the runner.

**Contributing**
- Feel free to open issues or PRs. Tests should accompany any substantive change.

**License**
- This project does not include an explicit license file. Add a `LICENSE` if you plan to open-source it.

If you'd like, I can also add a short GitHub Actions file to run the test suite automatically on pushes.
