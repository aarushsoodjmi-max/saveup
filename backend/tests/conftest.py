"""Shared pytest fixtures.

Requires a real, running MySQL and Redis -- consistent with the rest
of this project's "MySQL is the source of truth, Redis is cache/OTP/
rate-limiting only" architecture, and necessary for the concurrency
tests to exercise real InnoDB row locks (SQLite's ``FOR UPDATE`` is a
silent no-op, so it can't validate the ledger's core safety property).

Point ``TEST_DATABASE_URL`` / ``TEST_REDIS_URL`` at a *disposable*
database/Redis index before running the suite -- see README.md.
"""

import os
import uuid
from datetime import date

import pytest
import redis as redis_lib
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

os.environ.setdefault(
    "DATABASE_URL",
    "mysql+pymysql://saveup:saveup_dev_password@localhost:3306/saveup_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("OTP_DEBUG_EXPOSE", "true")

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", os.environ["DATABASE_URL"])
TEST_REDIS_URL = os.environ.get("TEST_REDIS_URL", os.environ["REDIS_URL"])

import app.models  # noqa: E402  (populates Base.metadata)
from app.core.database import Base  # noqa: E402
from app.core.dependencies import get_db  # noqa: E402
from app.core.redis import get_redis  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.models.user import User  # noqa: E402


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="session")
def session_factory(test_engine):
    return sessionmaker(bind=test_engine, autocommit=False, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def db_session(session_factory):
    """A plain, real session -- callers manage their own commits.

    Deliberately *not* a rollback-per-test wrapper: several tests below
    need changes to actually commit so a second thread/session can see
    them (that's the whole point of the concurrency tests). Cleanup
    happens by truncating tables after each test instead.
    """
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(autouse=True)
def _clean_database(test_engine):
    yield
    with test_engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))


@pytest.fixture()
def redis_client():
    client = redis_lib.Redis.from_url(TEST_REDIS_URL, decode_responses=True)
    client.flushdb()
    yield client
    client.flushdb()
    client.close()


@pytest.fixture()
def client(db_session, redis_client):
    def _override_get_db():
        yield db_session

    def _override_get_redis():
        yield redis_client

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    fastapi_app.dependency_overrides[get_redis] = _override_get_redis
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def make_user(db_session):
    """Factory fixture: create+commit a verified, active user directly
    (bypassing the OTP flow) for tests that just need an authenticated
    principal.
    """

    def _make(*, role: str = "USER", phone_number: str | None = None, name: str = "Test User") -> User:
        user = User(
            phone_number=phone_number or f"+1555{uuid.uuid4().int % 10_000_000:07d}",
            name=name,
            role=role,
            kyc_status="VERIFIED",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make


@pytest.fixture()
def auth_headers():
    def _headers(user: User) -> dict:
        token, _ = create_access_token(user.id, user.role)
        return {"Authorization": f"Bearer {token}"}

    return _headers
