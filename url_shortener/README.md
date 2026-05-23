# URL Shortener

A clean Django + DRF project with JWT auth, PostgreSQL, Scalar API docs, and a built-in frontend.

## Stack

- Django 5.1 + Django REST Framework
- PostgreSQL (via psycopg2)
- SimpleJWT — 1 day access / 7 day refresh tokens
- drf-spectacular — OpenAPI 3 schema generation
- django-scalar — Scalar API docs UI at `/api/docs/`
- django-environ — `.env` based config
- django-cors-headers

## Setup

```bash
# 1. Clone and enter the project
cd codealpha_tasks\url_shortener

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your DATABASE_URL and SECRET_KEY

# 5. Run migrations
python manage.py migrate

# 6. Start the development server
python manage.py runserver
```

## URLs

| URL | Description |
|-----|-------------|
| `http://localhost:8000/` | Frontend SPA |
| `http://localhost:8000/api/docs/` | Scalar API docs (test here) |
| `http://localhost:8000/api/schema/` | Raw OpenAPI JSON schema |
| `http://localhost:8000/api/auth/register/` | Register |
| `http://localhost:8000/api/auth/login/` | Login |
| `http://localhost:8000/api/auth/logout/` | Logout |
| `http://localhost:8000/api/auth/token/refresh/` | Refresh token |
| `http://localhost:8000/api/auth/me/` | Current user |
| `http://localhost:8000/api/urls/` | List / Create URLs |
| `http://localhost:8000/api/urls/<id>/` | Retrieve / Delete URL |
| `http://localhost:8000/<short_code>/` | Redirect to original URL |

## Environment variables

```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:password@localhost:5432/url_shortener_db
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:8000
```

## Settings

Switch environments with `DJANGO_SETTINGS_MODULE`:
- `config.settings.development` (default)
- `config.settings.production`