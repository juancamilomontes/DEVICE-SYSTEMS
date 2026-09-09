"""Pruebas del CRUD sobre base de datos.

Usa una base de datos SQLite EN MEMORIA solo para los tests, distinta de la real.
`app.dependency_overrides` reemplaza get_db por una sesión de prueba, y un
fixture recrea las tablas vacías antes de cada test (aislamiento).

Ejecutar con:  uv run pytest
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.connection import Base
from app.dependencies.database_dependency import get_db
from app.main import app

# Base de datos de prueba: SQLite en memoria (no toca device_systems.db).
engine_test = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)
AUTH = {"X-API-Key": "device-systems-2026"}


@pytest.fixture(autouse=True)
def reset_db():
    """Antes de cada test: borra y recrea las tablas (BD vacía)."""
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)
    yield


def crear(name="Test User", email="test@device.com", role="user"):
    """Helper: crea un usuario y devuelve la respuesta JSON."""
    return client.post("/users", json={"name": name, "email": email, "role": role})


# --- POST -------------------------------------------------------------------
def test_crear_usuario_ok():
    r = crear()
    assert r.status_code == 201
    body = r.json()
    assert body["id"] >= 1
    assert body["email"] == "test@device.com"
    assert "created_at" in body


def test_crear_email_duplicado():
    assert crear(email="dup@device.com").status_code == 201
    assert crear(email="dup@device.com").status_code == 400


def test_crear_nombre_corto():
    assert client.post("/users", json={"name": "ab", "email": "x@device.com"}).status_code == 422


def test_crear_email_invalido():
    assert client.post("/users", json={"name": "Valido", "email": "no-correo"}).status_code == 422


def test_crear_rol_invalido():
    r = client.post("/users", json={"name": "Valido", "email": "r@device.com", "role": "jefe"})
    assert r.status_code == 422


# --- GET --------------------------------------------------------------------
def test_listar_y_cabeceras():
    crear(email="a@device.com")
    crear(email="b@device.com")
    r = client.get("/users")
    assert r.status_code == 200
    assert len(r.json()) == 2
    assert r.headers["X-App-Name"] == "device_systems"
    assert r.headers["X-API-Version"] == "3.0"


def test_obtener_por_id():
    creado = crear().json()
    r = client.get(f"/users/{creado['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == creado["id"]


def test_obtener_inexistente():
    r = client.get("/users/9999")
    assert r.status_code == 404
    assert r.json()["detail"] == "Usuario no encontrado"


def test_filtrar_por_rol():
    crear(email="admin@device.com", role="admin")
    crear(email="user@device.com", role="user")
    r = client.get("/users", params={"role": "admin"})
    assert r.status_code == 200
    assert all(u["role"] == "admin" for u in r.json())
    assert len(r.json()) == 1


def test_filtrar_por_estado():
    crear(email="activo@device.com")
    r = client.get("/users", params={"is_active": "true"})
    assert all(u["is_active"] is True for u in r.json())


# --- PUT --------------------------------------------------------------------
def test_put_reemplaza():
    creado = crear(email="put@device.com").json()
    r = client.put(
        f"/users/{creado['id']}",
        json={"name": "Editado PUT", "email": "put@device.com", "role": "admin", "is_active": False},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Editado PUT"
    assert r.json()["role"] == "admin"


def test_put_inexistente():
    r = client.put("/users/9999", json={"name": "X Y Z", "email": "x@device.com", "role": "user", "is_active": True})
    assert r.status_code == 404


# --- PATCH ------------------------------------------------------------------
def test_patch_un_campo():
    creado = crear(email="patch@device.com").json()
    r = client.patch(f"/users/{creado['id']}", json={"role": "support"})
    assert r.status_code == 200
    assert r.json()["role"] == "support"
    assert r.json()["email"] == "patch@device.com"  # lo demás no cambia


def test_patch_vacio_400():
    creado = crear(email="vacio@device.com").json()
    assert client.patch(f"/users/{creado['id']}", json={}).status_code == 400


def test_patch_inexistente():
    assert client.patch("/users/9999", json={"role": "user"}).status_code == 404


# --- DELETE -----------------------------------------------------------------
def test_delete_ok_y_desaparece():
    creado = crear(email="del@device.com").json()
    r = client.delete(f"/users/{creado['id']}", headers=AUTH)
    assert r.status_code == 204
    assert client.get(f"/users/{creado['id']}").status_code == 404


def test_delete_sin_api_key():
    creado = crear(email="sinkey@device.com").json()
    assert client.delete(f"/users/{creado['id']}").status_code == 401


def test_delete_inexistente():
    assert client.delete("/users/9999", headers=AUTH).status_code == 404


# --- /info ------------------------------------------------------------------
def test_info():
    r = client.get("/info")
    assert r.status_code == 200
    assert r.json()["version"] == "3.0.0"
