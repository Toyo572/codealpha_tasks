# Restaurant Management System

A modular Django REST API for managing restaurant operations — orders, tables, reservations, menu, inventory, and reporting. Built with DRF ViewSets, JWT authentication, and DRF Spectacular for interactive API docs.

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Django 5.0 | Web framework |
| Django REST Framework | API layer |
| SimpleJWT | JWT authentication |
| drf-spectacular | OpenAPI schema + Swagger UI |
| django-environ | Environment variable management |
| django-filter | Query filtering |
| psycopg2 | PostgreSQL adapter |
| django-cors-headers | CORS support |

---

## Project Structure

```
restaurant_management/
├── config/                 # Settings, URLs, WSGI
├── core/               # Shared: pagination, exceptions, permissions, mixins
├── users/              # Custom user model, JWT auth, role management
├── menu/               # Categories and menu items
|── tables/             # Tables, reservations, availability checks
├── orders/             # Order lifecycle and processing
├── inventory/          # Stock tracking, auto-deduction, transactions
|── reports/            # Daily/monthly sales, low stock, inventory valuation
├── manage.py
├── requirements.txt
└── .env.example
```

---

## Setup

### 1. Clone and create virtual environment

```bash
git clone <repo-url>
cd restaurant_management
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
DEBUG=True
SECRET_KEY=your-very-secret-key-here
DATABASE_URL=postgres://user:password@localhost:5432/restaurant_db
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
JWT_ACCESS_TOKEN_LIFETIME_DAYS=1
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7
```

> SQLite fallback: if `DATABASE_URL` is omitted, SQLite is used automatically (good for local dev).

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Create a superuser (admin)

```bash
python manage.py createsuperuser
```

### 6. Start the development server

```bash
python manage.py runserver
```

---

## API Documentation

Open your browser and visit:

| UI | URL |
|---|---|
| Swagger UI | http://localhost:8000/api/schema/swagger-ui/ |
| Redoc | http://localhost:8000/api/schema/redoc/ |
| Raw OpenAPI schema | http://localhost:8000/api/schema/ |

> **Authenticate in Swagger**: Click "Authorize", enter `Bearer <your_access_token>`.

---

## API Endpoints

### Auth — `/api/v1/auth/`

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/v1/auth/register/` | Register new user | Public |
| POST | `/api/v1/auth/login/` | Login, receive JWT tokens | Public |
| POST | `/api/v1/auth/logout/` | Blacklist refresh token | Required |
| GET/PATCH | `/api/v1/auth/me/` | View or update profile | Required |
| POST | `/api/v1/auth/change-password/` | Change password | Required |
| POST | `/api/v1/auth/token/refresh/` | Refresh access token | Required |

### User Management — `/api/v1/auth/users/` (Admin only)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/auth/users/` | List all users |
| GET | `/api/v1/auth/users/{id}/` | Get user |
| PATCH | `/api/v1/auth/users/{id}/` | Update user |
| DELETE | `/api/v1/auth/users/{id}/` | Delete user |

### Menu — `/api/v1/menu/`

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/v1/menu/categories/` | List categories | Required |
| POST | `/api/v1/menu/categories/` | Create category | Staff/Admin |
| GET/PATCH/DELETE | `/api/v1/menu/categories/{id}/` | Category detail | Staff/Admin (write) |
| GET | `/api/v1/menu/items/` | List menu items | Required |
| POST | `/api/v1/menu/items/` | Create menu item | Staff/Admin |
| GET/PATCH/DELETE | `/api/v1/menu/items/{id}/` | Menu item detail | Staff/Admin (write) |

**Menu item filters**: `?category=1&availability=available&is_vegetarian=true&min_price=500&max_price=5000`

### Tables — `/api/v1/tables/`

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/v1/tables/` | List tables | Required |
| POST | `/api/v1/tables/` | Add table | Staff/Admin |
| PATCH | `/api/v1/tables/{id}/status/` | Update table status | Staff/Admin |
| GET | `/api/v1/tables/available/` | Check available tables | Required |
| GET | `/api/v1/tables/reservations/` | List reservations | Required |
| POST | `/api/v1/tables/reservations/` | Make a reservation | Required |
| PATCH | `/api/v1/tables/reservations/{id}/status/` | Update reservation status | Staff/Admin |

**Available tables query**: `?date=2025-12-25&time=19:00&party_size=4&duration_minutes=90`

### Orders — `/api/v1/orders/`

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/v1/orders/` | List orders (own or all) | Required |
| POST | `/api/v1/orders/` | Place an order | Required |
| GET | `/api/v1/orders/{id}/` | Order detail | Required |
| PATCH | `/api/v1/orders/{id}/status/` | Transition order status | Staff/Admin |
| PATCH | `/api/v1/orders/{id}/payment/` | Update payment status | Staff/Admin |

**Order status flow**: `pending → confirmed → preparing → ready → served → completed`

### Inventory — `/api/v1/inventory/`

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/v1/inventory/items/` | List inventory items | Staff/Admin |
| POST | `/api/v1/inventory/items/` | Add inventory item | Staff/Admin |
| PATCH | `/api/v1/inventory/items/{id}/` | Update item | Staff/Admin |
| POST | `/api/v1/inventory/items/{id}/restock/` | Restock item | Staff/Admin |
| GET | `/api/v1/inventory/ingredients/` | List ingredient mappings | Staff/Admin |
| POST | `/api/v1/inventory/ingredients/` | Map ingredient to menu item | Staff/Admin |
| GET | `/api/v1/inventory/transactions/` | Stock transaction history | Staff/Admin |
| POST | `/api/v1/inventory/transactions/` | Record manual transaction | Staff/Admin |

**Low stock filter**: `?low_stock=true`

### Reports — `/api/v1/reports/`

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/api/v1/reports/daily-sales/` | Daily sales report | Staff/Admin |
| GET | `/api/v1/reports/monthly-sales/` | Monthly sales report | Staff/Admin |
| GET | `/api/v1/reports/low-stock/` | Low stock alerts | Staff/Admin |
| GET | `/api/v1/reports/inventory-valuation/` | Inventory total value | Staff/Admin |
| GET | `/api/v1/reports/table-utilization/` | Table & reservation stats | Staff/Admin |

**Report query params**:
- Daily: `?date=2025-07-15`
- Monthly: `?year=2025&month=7`

---

## User Roles

| Role | Access Level |
|---|---|
| `customer` | Own orders, own reservations, read menu/tables |
| `staff` | All of the above + write menu, manage orders/reservations/inventory |
| `admin` | Full access including user management |

---

## Key Design Decisions

- **ViewSets only** — every endpoint uses `ModelViewSet` or `GenericViewSet`. No `APIView` or `@api_view` anywhere. All actions accept a serializer.
- **Consistent response shape** — all responses are wrapped: `{"success": true, "data": {...}}` for success and `{"success": false, "status_code": 4xx, "errors": {...}}` for errors.
- **Automatic inventory deduction** — when an order is marked `completed`, Django signals auto-deduct ingredients from stock based on `MenuItemIngredient` mappings.
- **Order status guard** — `processors.py` enforces valid status transitions. Invalid jumps return a 400 error with allowed next states.
- **JWT tokens** — access token lives 1 day, refresh token 7 days. Refresh token is blacklisted on logout.

---

## Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | — | Django secret key (required) |
| `DEBUG` | `False` | Debug mode |
| `DATABASE_URL` | SQLite | Database connection string |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed host headers |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | CORS origins |
| `JWT_ACCESS_TOKEN_LIFETIME_DAYS` | `1` | Access token lifetime |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | `7` | Refresh token lifetime |