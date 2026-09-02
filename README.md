# SaveUp

SaveUp is a goal-based savings platform. Users create savings goals, deposit
money into locked vaults, track progress, and — for MEDIUM/HARD lock goals —
request emergency withdrawals through an emergency-contact approval flow.

This repository contains the backend API (FastAPI + MySQL + Redis). See
`docs/` for the original product requirements, database schema, system
design, and API reference that this implementation follows.

## Stack

- **FastAPI** (sync route handlers) + **Pydantic v2** for request/response schemas
- **SQLAlchemy 2.0** (typed `Mapped[...]` models) + **Alembic** for migrations
- **MySQL** — source of truth for all data, including money
- **Redis** — OTP storage, rate limiting, and idempotency pre-checks only; **never balances**
- **PyJWT** — short-lived access tokens + rotated opaque refresh tokens

## Architecture

Modular monolith with a strict layering convention:

```
app/api/v1/        Route handlers — thin, no business logic
app/schemas/        Pydantic request/response models
app/services/       Business logic, transaction boundaries
app/repositories/   Data access (SQLAlchemy queries), one per model
app/models/         SQLAlchemy ORM models
app/core/           Config, DB/Redis clients, security, dependencies, errors
```

The ledger (`app/services/ledger_service.py`) is the safety-critical core:
every deposit, withdrawal, and refund flows through it, and it enforces —
- `Decimal` everywhere money is touched (never float)
- `SELECT ... FOR UPDATE` row locking on the target goal before any balance change
- One atomic DB transaction per operation (balance change + ledger row insert commit together)
- Idempotency via a `UNIQUE` DB constraint (not just an in-memory check) so retried/duplicated requests can never double-apply
- No negative balances

---

## Prerequisites

- Python 3.11+
- MySQL 8.x running locally (or reachable)
- Redis 6.x+ running locally (or reachable)

## Setup (from a fresh clone)

```bash
cd backend

# 1. Create and activate a virtualenv
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# .env already works against the default MySQL/Redis credentials below;
# edit it if your local MySQL/Redis differ.

# 4. Create the database
mysql -u root -p -e "CREATE DATABASE saveup CHARACTER SET utf8mb4;"

# 5. Run migrations
alembic upgrade head

# 6. Start the API
uvicorn app.main:app --reload --port 8000
```

The API is now running at `http://localhost:8000`.

- Interactive docs (Swagger UI): `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check (verifies DB + Redis connectivity): `http://localhost:8000/health`

### Quick manual sanity checks

```bash
python scripts/check_config.py   # prints the resolved DATABASE_URL / REDIS_URL
python scripts/check_db.py       # opens a real connection and runs SELECT 1
```

---

## Running the tests

The test suite runs against a **real** MySQL database and a **real** Redis
instance (a disposable one) — not SQLite or an in-memory fake — because the
concurrency tests exercise actual `SELECT ... FOR UPDATE` row locks, which
SQLite silently ignores.

```bash
# 1. Create a disposable test database
mysql -u root -p -e "CREATE DATABASE saveup_test CHARACTER SET utf8mb4;"

# 2. Point the test run at it (defaults shown; override if needed)
export TEST_DATABASE_URL="mysql+pymysql://root:sample_password@localhost:3306/saveup_test"
export TEST_REDIS_URL="redis://localhost:6379/15"   # a spare, disposable Redis DB index

# 3. Run the suite
pytest

# With coverage:
pytest --cov=app --cov-report=term-missing
```

`tests/conftest.py` creates all tables via `Base.metadata.create_all()` once
per test session and truncates every table after each test — it does not
touch your dev database as long as `TEST_DATABASE_URL` points somewhere
different, which the defaults above do (`saveup_test` vs `saveup`, Redis DB
`15` vs `0`).

What's covered: OTP send/verify + expiry + rate limiting, JWT refresh
rotation and reuse-detection, goal CRUD and validation, ledger deposits/
withdrawals/refunds, **concurrent deposits and withdrawals** (real threads +
real DB connections proving no lost updates and no overdraws), idempotency
under both sequential replay and a genuine concurrent race, the payment
webhook (signature verification + idempotent redelivery), the full
emergency-withdrawal state machine (request → OTP approval → cooldown →
completion, plus rejection/cancellation edge cases), RBAC, notifications,
achievements, and streaks.

---

## Database migrations

Migrations live in `backend/alembic/versions/`, applied in this order:

| Revision | Adds |
|---|---|
| `90efce4a924b` | `users` |
| `a1b2c3d4e5f6` | `users.role` (RBAC) |
| `b2c3d4e5f6a7` | `refresh_tokens` |
| `c3d4e5f6a7b8` | `emergency_contacts` |
| `d4e5f6a7b8c9` | `goals` |
| `e5f6a7b8c9d0` | `transactions` (the ledger) |
| `f6a7b8c9d0e1` | `payment_orders` |
| `a7b8c9d0e1f2` | `payment_attempts` |
| `b8c9d0e1f2a3` | `withdrawal_requests` |
| `c9d0e1f2a3b4` | `notifications` |
| `d0e1f2a3b4c5` | `achievements` |
| `e1f2a3b4c5d6` | `user_achievements` |
| `f2a3b4c5d6e7` | `streaks` |

```bash
alembic upgrade head        # apply all
alembic downgrade -1        # roll back one
alembic history              # list the chain
```

---

## Seeding achievements

Achievements are admin-curated data, not code — there's no seed script yet
(see Known limitations). To try the achievement-unlock flow locally, insert
a row directly, e.g.:

```sql
INSERT INTO achievements (id, code, title, metric, required_value, created_at)
VALUES (UNHEX(REPLACE(UUID(), '-', '')), 'FIRST_HUNDRED', 'First ₹100 Saved', 'TOTAL_SAVED', 100.00, NOW());
```

---

## API overview

Full endpoint list in `docs/api_documentation.md`. Highlights:

- `POST /api/v1/auth/send-otp`, `POST /api/v1/auth/verify-otp`, `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`
- `GET/PUT /api/v1/users/me`
- `POST/GET/PUT/DELETE /api/v1/goals`, plus `/pause`, `/resume`, `/archive`, `/withdraw` (EASY lock only)
- `POST /api/v1/emergency-contacts`
- `POST /api/v1/payments/create-order`, `POST /api/v1/payments/verify`, `POST /api/v1/payments/webhook`
- `GET /api/v1/transactions`
- `POST /api/v1/withdrawals` + `/approve`, `/reject`, `/cancel`, `/complete`, `/resend-otp` (MEDIUM/HARD lock goals)
- `GET /api/v1/notifications`, `/unread-count`, `PATCH /{id}/read`
- `GET /api/v1/achievements`, `/achievements/unlocked`, `/streak`
- `GET /api/v1/dashboard`
- `/api/v1/admin/*` — RBAC-protected (users, KYC, withdrawal review, dashboard summary, transaction search)

Every response error uses one JSON shape:

```json
{
  "success": false,
  "error": { "code": "INSUFFICIENT_BALANCE", "message": "...", "details": {} },
  "request_id": "..."
}
```

### Trying the emergency-withdrawal flow without a real SMS provider

`OTP_DEBUG_EXPOSE=true` (the `.env.example` default, off automatically when
`ENVIRONMENT=production`) echoes generated OTPs back in API responses —
`debug_otp` on `/auth/send-otp` and on `POST /withdrawals` — so the full
OTP-gated flows can be exercised end to end without wiring up Twilio/MSG91.

---

## Design decisions worth knowing

- **EASY-lock goals bypass the emergency workflow entirely.** They carry no
  lock guarantee, so `POST /goals/{id}/withdraw` withdraws immediately
  through the ledger. `POST /withdrawals` (the emergency-contact/OTP/
  cooldown flow) only accepts MEDIUM and HARD lock goals, per the product
  requirements.
- **Withdrawal approval/rejection endpoints are intentionally
  unauthenticated.** The emergency contact has no SaveUp account — the
  unguessable request UUID plus the one-time OTP sent to their phone is the
  credential, the same trust model as an email verification link.
- **Refresh token rotation** revokes the entire token chain for a user the
  moment an already-rotated-out (or otherwise revoked) refresh token is
  presented again — treated as a compromise signal, not just an error.
- **Deposits only happen through the payment order + webhook/verify flow**
  in the public API (there's no "manually add money" endpoint) — this
  matches the documented API surface. `LedgerService.deposit()` itself is
  general-purpose and is what both the webhook handler and any future admin
  tooling would call.
- **MySQL has no `TIMESTAMP WITH TIME ZONE`.** `app/core/time_utils.py`
  documents and centralizes the resulting naive/aware datetime handling —
  see that file before touching any code that compares a DB-sourced
  datetime against `datetime.now()`.

## Known limitations / not yet built

- **Challenges** (`GET /challenges`, `POST /challenges/{id}/join`) are
  present as routes (per `docs/api_documentation.md`) but return an empty/
  placeholder result — there's no `Challenge` model or table. Out of scope
  for this pass; flagged rather than faked.
- **`PUT /settings`** (user notification/app preferences) from the API doc
  is not implemented — no `Settings` model exists yet.
- **No achievement seed data or admin endpoint to create achievements** —
  insert rows directly (see above) until an admin CRUD endpoint exists.
- **No device/session management** beyond refresh-token rotation (no
  per-device listing/"log out other devices").
- **`POST /withdrawals/{id}/complete` is not scheduler-driven.** In
  production, a cron/worker should call it automatically the instant
  `cooldown_ends_at` passes; today it requires the user (or a manually
  configured cron hitting the same endpoint) to trigger it, since there's
  no background job runner in this stack.
- **KYC verification is admin-manual only** — no document upload/OCR/
  third-party KYC provider integration, matching "mock everything, no real
  gateways" scope.
- **This code has not been executed.** It was written and hand-reviewed in
  an environment without network access to install FastAPI/SQLAlchemy/etc.
  or a running MySQL/Redis, so it could not be run or the test suite
  executed before delivery. Budget time for a first-run debugging pass —
  most likely trouble spots are import paths and any SQLAlchemy 2.0 /
  Pydantic v2 API surface that shifted between versions.
