"""Configuración compartida de las pruebas (base de datos en memoria + auth).

- BD SQLite en memoria aislada (no toca device_systems.db).
- Rate limiting desactivado por defecto (los tests que lo prueban lo activan).
- Fixtures que registran usuarios y devuelven cabeceras con el token JWT.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (registra User, Device y Loan)
from app.database.connection import Base
from app.dependencies.database_dependency import get_db
from app.main import app
from app.middlewares.rate_limit import limiter

# Los tests normales no deben chocar con los límites de peticiones.
limiter.enabled = False

engine_test = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine_test)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    """Recrea las tablas vacías antes de cada test."""
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def make_headers(client):
    """Devuelve una función que registra un usuario y da sus cabeceras con token."""

    def _make(email, password="Password1", role="user", name="Usuario Test"):
        client.post("/auth/register", json={
            "name": name, "email": email, "password": password, "role": role,
        })
        r = client.post("/auth/login", data={"username": email, "password": password})
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    return _make


@pytest.fixture
def admin_headers(make_headers):
    return make_headers("admin@device.com", role="admin", name="Admin User")


@pytest.fixture
def support_headers(make_headers):
    return make_headers("support@device.com", role="support", name="Support User")


@pytest.fixture
def user_headers(make_headers):
    return make_headers("user@device.com", role="user", name="Normal User")
