"""Configuración compartida de las pruebas.

Todas las pruebas usan una base de datos SQLite EN MEMORIA (aislada de
device_systems.db). Se reemplaza get_db por una sesión de prueba y antes de
cada test se recrean las tablas vacías.
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
