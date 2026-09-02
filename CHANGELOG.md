# Changelog — SaveUp Backend MVP

This session took the project from an infrastructure skeleton (FastAPI
bootstrap, config, DB connection, one `users` migration, and empty stub
files for everything else) to a functionally complete backend MVP. Nothing
described below existed before this pass except where explicitly noted as
"fixed" or "extended."

## Fixed (bugs in the pre-existing code)

- `alembic/versions/90efce4a924b_create_users_table.py` referenced
  `app.core.uuid_type.UUIDType` without importing the `app` module —
  `alembic upgrade head` would have crashed immediately on a fresh clone.
  Fixed the import and removed an invalid `length=16` kwarg the custom
  `UUIDType` doesn't accept.
- `requirements.txt` was missing `PyMySQL`, the driver the configured
  `mysql+pymysql://` `DATABASE_URL` actually requires — the app could not
  have connected to MySQL at all. Also added `email-validator` (required
  by Pydantic's `EmailStr`, used in profile updates) and `pytest`/
  `pytest-cov` for the new test suite.
- `test_config.py` / `test_db.py` lived at the backend root with `test_`
  filenames but no test functions — `pytest`'s default discovery would
  have collected them and `test_db.py` would open a real DB connection at
  *collection* time, breaking any test run without one available. Moved
  both to `scripts/check_config.py` / `scripts/check_db.py` and added
  `pytest.ini` scoping discovery to `tests/`.
- No `__init__.py` in any package directory (worked only via Python's
  implicit namespace packages). Added them throughout for reliability.
- `.gitignore` was empty — added standard Python/env/test-artifact
  exclusions.

## Added — Infrastructure

- Expanded `Settings` (JWT, OTP, rate limiting, idempotency, CORS,
  pagination, mock-provider secrets) with a cached singleton.
- Redis client + `get_redis` dependency.
- JWT access-token issuance/verification, OTP hashing (HMAC-SHA256 with a
  server pepper), and opaque-refresh-token hashing (`app/core/security.py`).
- Structured `AppError` hierarchy + global exception handlers producing one
  consistent JSON error envelope.
- Request-ID middleware + structured logging setup.
- `get_current_user` / `require_roles` / `require_admin` dependencies,
  pagination and idempotency-key dependencies.
- `app/core/time_utils.py` centralizing the MySQL naive/aware datetime
  handling (`DateTime(timezone=True)` round-trips as naive UTC via PyMySQL).
- FastAPI app factory (`main.py`): CORS, middleware, exception handlers,
  all routers, `lifespan` startup/shutdown DB+Redis connectivity checks,
  `/health` endpoint.

## Added — Data model (10 new SQLAlchemy models, 12 new Alembic migrations)

`User.role` (RBAC), `RefreshToken`, `EmergencyContact`, `Goal`,
`Transaction` (the unified ledger), `PaymentOrder`, `PaymentAttempt`,
`WithdrawalRequest`, `Notification`, `Achievement` + `UserAchievement`,
`Streak`. See root `README.md` → "Database migrations" for the full,
ordered revision list.

## Added — Business logic (`app/services/`)

- **`ledger_service.py`** — the core: `Decimal`-only, row-locked
  (`SELECT ... FOR UPDATE`), atomic deposit/withdraw/refund with
  DB-unique-constraint-backed idempotency. Everything else that moves
  money calls into this.
- **`otp_service.py`** — Redis-backed OTP issuance/verification with
  expiry and attempt limits.
- **`token_service.py`** — refresh-token issuance and rotation with
  reuse-detection (a replayed, already-rotated token revokes the whole
  chain).
- **`auth_service.py`, `user_service.py`, `goal_service.py`** — auth
  orchestration, profile updates, goal CRUD/state transitions.
- **`payment_service.py`** — order creation + a signature-verified,
  idempotent webhook handler that shares one atomic commit with the
  ledger deposit it triggers.
- **`withdrawal_service.py`** — the full emergency-withdrawal state
  machine (request → contact OTP approval/rejection → lock-type cooldown
  → completion; cancellation rules differ by lock type) plus an admin
  override path.
- **`notification_service.py`, `streak_service.py`,
  `achievement_service.py`** — best-effort follow-ups after a deposit
  commits (failures here are logged, never roll back money).
- **`admin_service.py`** — user list w/ per-user totals, KYC/active-status
  updates, dashboard aggregates, transaction search.
- **`sms_provider.py`, `push_provider.py`, `payment_provider.py`** — mock
  providers behind small interfaces so a real SMS/push/gateway integration
  is a drop-in swap, not a rewrite.
- **`rate_limit_service.py`, `idempotency_service.py`** — Redis-backed
  fixed-window rate limiting and a fast-path idempotency pre-check (the DB
  constraint remains the actual guarantee).

## Added — API surface (`app/api/v1/`, all previously empty stubs)

Auth, Users, Goals (+ pause/resume/archive/direct-withdraw for EASY-lock
goals), Emergency Contacts (new), Payments, Transactions (new), Withdrawals,
Notifications, Achievements/Streak, Challenges (placeholder — see
limitations), Dashboard, Admin (new, RBAC-protected). Full route list in
root `README.md` → "API overview".

## Added — Tests (`backend/tests/`, previously empty)

Real-MySQL/real-Redis pytest suite: `conftest.py` fixtures, then auth
(OTP/JWT/refresh rotation/rate limits), goals (CRUD/validation), the
ledger (deposit/withdraw/refund, **concurrent-thread tests for lost-update
and overdraw prevention**, sequential and **concurrent** idempotency),
payment webhook (signature verification, idempotent redelivery), the full
emergency-withdrawal flow, RBAC, notifications/achievements/streaks.

## Added — Documentation

- Root `README.md` (was empty) — setup, run, test, migrations, API
  overview, explicit design decisions, and known limitations.
- `.env.example` (new) documenting every setting.
- Short "implementation status" notes added to `docs/system_design.md`,
  `docs/api_documentation.md`, and `docs/database_schema.md` pointing out
  where the shipped code follows vs. deviates from those design docs
  (originals otherwise left intact).

## Commands to run

See root `README.md` for the full walkthrough. Short version:

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
mysql -u root -p -e "CREATE DATABASE saveup CHARACTER SET utf8mb4;"
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# tests (separate disposable DB):
mysql -u root -p -e "CREATE DATABASE saveup_test CHARACTER SET utf8mb4;"
export TEST_DATABASE_URL="mysql+pymysql://root:sample_password@localhost:3306/saveup_test"
export TEST_REDIS_URL="redis://localhost:6379/15"
pytest
```

## Remaining production limitations

See root `README.md` → "Known limitations / not yet built" for the full,
current list (challenges, settings endpoint, achievement seeding/admin
CRUD, device/session management, scheduler-driven withdrawal completion,
KYC automation). The single most important caveat: **this code was written
and hand-reviewed without the ability to execute it** — no network access
to install FastAPI/SQLAlchemy/etc. and no running MySQL/Redis were
available in the environment this was built in. Every file was syntax-
checked and cross-checked for import correctness, but a first-run
debugging pass against real MySQL/Redis should be expected before this
is treated as verified-working.
