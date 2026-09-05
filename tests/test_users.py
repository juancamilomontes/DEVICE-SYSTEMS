"""Pruebas automáticas del recurso `users` con TestClient de FastAPI.

Ejecutar con:  uv run pytest
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_listar_usuarios():
    r = client.get("/users")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    # Las cabeceras personalizadas deben venir en la respuesta.
    assert r.headers["X-App-Name"] == "device_systems"
    assert r.headers["X-API-Version"] == "1.0"


def test_filtrar_por_rol():
    r = client.get("/users", params={"role": "admin"})
    assert r.status_code == 200
    assert all(u["role"] == "admin" for u in r.json())


def test_filtrar_por_activo():
    r = client.get("/users", params={"is_active": "false"})
    assert r.status_code == 200
    assert all(u["is_active"] is False for u in r.json())


def test_obtener_usuario_existente():
    r = client.get("/users/1")
    assert r.status_code == 200
    assert r.json()["id"] == 1


def test_obtener_usuario_inexistente():
    r = client.get("/users/9999")
    assert r.status_code == 404


def test_crear_usuario_ok():
    r = client.post(
        "/users",
        json={"name": "Test User", "email": "test.crear@device.com", "role": "user"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "test.crear@device.com"
    assert "id" in body


def test_crear_usuario_email_duplicado():
    payload = {"name": "Dup User", "email": "dup@device.com"}
    assert client.post("/users", json=payload).status_code == 201
    # Segundo intento con el mismo correo -> 409.
    assert client.post("/users", json=payload).status_code == 409


def test_crear_usuario_nombre_corto():
    r = client.post("/users", json={"name": "ab", "email": "corto@device.com"})
    assert r.status_code == 422


def test_crear_usuario_email_invalido():
    r = client.post("/users", json={"name": "Nombre Valido", "email": "no-es-correo"})
    assert r.status_code == 422


def test_crear_usuario_rol_invalido():
    r = client.post(
        "/users",
        json={"name": "Nombre Valido", "email": "rol@device.com", "role": "jefe"},
    )
    assert r.status_code == 422
