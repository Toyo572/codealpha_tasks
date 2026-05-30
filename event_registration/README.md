# Event Registration System

Django REST Framework API with JWT authentication, Scalar UI for browser testing.

## Stack
- Django 4.2 + DRF 3.15
- JWT via `djangorestframework-simplejwt` (1-day access / 7-day refresh)
- `django-environ` for environment variables
- `drf-spectacular` → OpenAPI 3 schema → Scalar browser UI
- PostgreSQL 

## Project Layout
```
event_registration/
├── config/
│   ├── settings/
│   │   ├── base.py       ← shared settings
│   │   ├── dev.py        ← DEBUG=True
│   │   └── prod.py       ← production overrides
│   └── urls.py
└
├── core/             ← BaseAPIView, pagination, exceptions, responses, permissions
├── accounts/         ← User model, auth (register/login/logout/refresh/me)
├── events/           ← Event & Category models, public + organizer endpoints
└── registrations/    ← Registration model, register/cancel/list endpoints
```

## Quick Start

```bash
cp .env.example .env          # fill in your values
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Browse API at: http://localhost:8000/api/docs/  (Scalar UI)

## API Endpoints

### Auth  — /api/v1/accounts/
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | /register/ | Public | Create attendee or organizer account |
| POST | /login/ | Public | Get access + refresh tokens |
| POST | /logout/ | Bearer | Blacklist refresh token |
| POST | /token/refresh/ | Public | Exchange refresh → new access |
| GET  | /me/ | Bearer | View own profile |
| PATCH | /me/ | Bearer | Update own profile |
| POST | /me/change-password/ | Bearer | Change password |

### Events  — /api/v1/events/
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | / | Public | List published events (paginated, filterable) |
| GET | /<id>/ | Public | Event detail |
| GET | /categories/ | Bearer | List categories |
| POST | /categories/ | Organizer | Create category |
| GET | /manage/ | Organizer | List own events |
| POST | /manage/ | Organizer | Create event |
| GET | /manage/<id>/ | Organizer | Get own event |
| PATCH | /manage/<id>/ | Organizer | Update own event |
| DELETE | /manage/<id>/ | Organizer | Delete own event |

### Registrations  — /api/v1/registrations/
| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | / | Bearer | Register for an event |
| GET | /me/ | Bearer | List my registrations |
| POST | /<id>/cancel/ | Bearer | Cancel a registration |
| GET | /event/<event_id>/ | Organizer | View registrations for own event |

## Response Shape (consistent across all endpoints)

### Success
```json
{ "success": true, "message": "...", "data": { ... } }
```

### Paginated list
```json
{
  "success": true, "message": "Success",
  "data": {
    "count": 42, "total_pages": 3, "current_page": 1,
    "next": "...", "previous": null,
    "results": [ ... ]
  }
}
```

### Error
```json
{ "success": false, "message": "...", "errors": { "field": "message" } }
```

## Environment Variables (.env)
```
SECRET_KEY=...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://user:pass@localhost:5432/event_db
```

## PostgreSQL Setup
```bash
createdb event_registration
# In .env:
DATABASE_URL=postgres://postgres:password@localhost:5432/event_registration
python manage.py migrate
```
