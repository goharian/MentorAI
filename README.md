
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
