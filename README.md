# AtoZSHIP

A shipment and delivery management API built with FastAPI. Sellers submit shipments, the system auto-assigns them to eligible delivery partners based on serviceable zip codes and handling capacity, and customers can track and review their deliveries.

## Tech Stack

| Component | Technology |
| --- | --- |
| Framework | FastAPI |
| Database | PostgreSQL (asyncpg) |
| ORM | SQLModel (SQLAlchemy 2.0) |
| Migrations | Alembic |
| Task Queue | Celery |
| Broker / Cache | Redis |
| Email | FastAPI-Mail (Gmail SMTP) |
| Auth | JWT (PyJWT) + OAuth2 |
| Password Hashing | pwdlib (Argon2) |
| Templates | Jinja2 |

---

## Prerequisites

- Python 3.13+
- PostgreSQL
- Redis

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/christianishimwe/AtoZSHIP.git
cd AtoZSHIP
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
# PostgreSQL
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=atozship
POSTGRES_PORT=5432
POSTGRES_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/atozship

# JWT
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# App
APP_BASE_URL=http://localhost:8000

# Email (Gmail)
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_gmail_app_password
MAIL_FROM=your_email@gmail.com
MAIL_FROM_NAME=AtoZSHIP
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
VALIDATE_CERTS=false
```

> For Gmail, generate an [App Password](https://myaccount.google.com/apppasswords) rather than using your account password.

### 5. Start PostgreSQL and Redis

Make sure both services are running before continuing.

```bash
# macOS (Homebrew)
brew services start postgresql
brew services start redis

# Linux (systemd)
sudo systemctl start postgresql
sudo systemctl start redis
```

### 6. Run database migrations

```bash
alembic upgrade head
```

### 7. Start the Celery worker

Open a new terminal, activate the virtual environment, then run:

```bash
celery -A app.worker.tasks worker --loglevel=info
```

Celery handles all outbound emails (verification, password reset, shipment status notifications) asynchronously so they don't block the API.

### 8. Start the API server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## API Overview

### Sellers (`/seller`)

| Method | Path | Description | Auth |
| --- | --- | --- | --- |
| POST | `/seller/signup` | Register a new seller | No |
| POST | `/seller/login` | Login (email must be verified) | No |
| GET | `/seller/logout` | Logout (blacklists JWT) | Yes |
| GET | `/seller/` | Get seller profile | Yes |
| GET | `/seller/verify` | Verify email via token | No |
| GET | `/seller/forgot_password` | Send password reset email | No |
| GET | `/seller/password_reset_form` | Password reset form | No |
| POST | `/seller/reset_password` | Submit new password | No |

### Delivery Partners (`/partner`)

| Method | Path | Description | Auth |
| --- | --- | --- | --- |
| POST | `/partner/signup` | Register a new delivery partner | No |
| POST | `/partner/login` | Login (email must be verified) | No |
| GET | `/partner/logout` | Logout (blacklists JWT) | Yes |
| POST | `/partner/` | Update partner profile | Yes |
| GET | `/partner/verify` | Verify email via token | No |
| GET | `/partner/forgot_password` | Send password reset email | No |
| GET | `/partner/password_reset_form` | Password reset form | No |
| POST | `/partner/reset_password` | Submit new password | No |

### Shipments (`/shipment`)

| Method | Path | Description | Auth |
| --- | --- | --- | --- |
| POST | `/shipment/` | Submit a new shipment | Seller |
| GET | `/shipment/` | Get shipment by ID | Seller |
| PATCH | `/shipment/` | Update shipment status/location | Partner |
| GET | `/shipment/cancel` | Cancel a shipment | Seller |
| GET | `/shipment/track` | Track shipment (HTML page) | No |
| GET | `/shipment/review` | Review form (token-based) | No |
| POST | `/shipment/review` | Submit a review (token-based) | No |
| POST | `/shipment/tag` | Add a tag to a shipment | Yes |
| DELETE | `/shipment/tag` | Remove a tag from a shipment | Yes |
| GET | `/shipment/tagged` | Get all shipments by tag name | Yes |

---

## Key Concepts

**Automatic partner assignment** — When a seller submits a shipment, the system picks an eligible delivery partner whose serviceable zip codes include the shipment's destination and who has remaining handling capacity.

**Shipment timeline** — Every status change (placed → shipped → in_transit → delivered/cancelled) creates a `ShipmentEvent` record and triggers an email notification to the client via Celery.

**Token-based review flow** — After delivery, a signed URL is emailed to the client. The token encodes the shipment ID and is validated server-side, so no account is required to leave a review.

**JWT blacklisting** — On logout, the token's `jti` claim is stored in Redis. Every authenticated request checks this blacklist, making logout truly stateless.

---

## Database Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "describe your change"

# Roll back one migration
alembic downgrade -1

# Check current migration state
alembic current
```

---

## Project Structure

```text
AtoZSHIP/
├── app/
│   ├── main.py               # App entry point and lifespan handler
│   ├── config.py             # Settings (DB, Redis, email, app)
│   ├── utils.py              # JWT helpers, token generation
│   ├── api/
│   │   ├── router.py         # Master router
│   │   ├── dependencies.py   # Dependency injection (session, services, auth)
│   │   ├── routers/          # Endpoint handlers
│   │   └── schemas/          # Pydantic request/response schemas
│   ├── core/
│   │   └── security.py       # OAuth2 schemes
│   ├── database/
│   │   ├── models.py         # SQLModel table definitions
│   │   ├── session.py        # Async session factory
│   │   └── redis.py          # JWT blacklist functions
│   ├── services/             # Business logic
│   │   ├── base.py           # Generic CRUD
│   │   ├── user.py           # Auth, email verification, password reset
│   │   ├── seller.py
│   │   ├── delivery_partner.py
│   │   ├── shipment.py
│   │   ├── shipment_event.py # Event creation + email notifications
│   │   └── tag.py
│   ├── worker/
│   │   └── tasks.py          # Celery tasks (email sending)
│   └── templates/            # Jinja2 HTML templates (email + web)
└── migrations/               # Alembic migration versions
```
