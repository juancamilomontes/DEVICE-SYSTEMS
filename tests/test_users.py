"""Pruebas automáticas del CRUD completo del recurso `users`.

Ejecutar con:  uv run pytest
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# Cabecera necesaria para el endpoint DELETE (autenticación simulada).
AUTH = {"X-API-Key": "device-systems-2026"}


# --- GET --------------------------------------------------------------------
def test_listar_usuarios():
    r = client.get("/users")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
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
    assert r.json()["detail"] == "Usuario no encontrado"


# --- POST -------------------------------------------------------------------
def test_crear_usuario_ok():
    r = client.post("/users", json={"name": "Test User", "email": "test.crear@device.com", "role": "user"})
    assert r.status_code == 201
    assert "id" in r.json()


def test_crear_usuario_email_duplicado():
    payload = {"name": "Dup User", "email": "dup@device.com"}
    assert client.post("/users", json=payload).status_code == 201
    assert client.post("/users", json=payload).status_code == 400


def test_crear_usuario_nombre_corto():
    assert client.post("/users", json={"name": "ab", "email": "corto@device.com"}).status_code == 422


def test_crear_usuario_email_invalido():
    assert client.post("/users", json={"name": "Nombre Valido", "email": "no-es-correo"}).status_code == 422


def test_crear_usuario_rol_invalido():
    r = client.post("/users", json={"name": "Nombre Valido", "email": "rol@device.com", "role": "jefe"})
    assert r.status_code == 422


# --- PUT --------------------------------------------------------------------
def test_put_reemplaza_usuario():
    creado = client.post("/users", json={"name": "Para PUT", "email": "put@device.com"}).json()
    r = client.put(
        f"/users/{creado['id']}",
        json={"name": "Editado PUT", "email": "put@device.com", "role": "admin", "is_active": False},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Editado PUT"
    assert r.json()["role"] == "admin"


def test_put_usuario_inexistente():
    r = client.put("/users/9999", json={"name": "X Y Z", "email": "x@device.com", "role": "user", "is_active": True})
    assert r.status_code == 404


# --- PATCH ------------------------------------------------------------------
def test_patch_actualiza_un_campo():
    creado = client.post("/users", json={"name": "Para PATCH", "email": "patch@device.com"}).json()
    r = client.patch(f"/users/{creado['id']}", json={"role": "support"})
    assert r.status_code == 200
    assert r.json()["role"] == "support"
    assert r.json()["name"] == "Para PATCH"  # lo demás no cambia


def test_patch_vacio_da_400():
    creado = client.post("/users", json={"name": "Patch Vacio", "email": "vacio@device.com"}).json()
    r = client.patch(f"/users/{creado['id']}", json={})
    assert r.status_code == 400


def test_patch_usuario_inexistente():
    assert client.patch("/users/9999", json={"role": "user"}).status_code == 404


# --- DELETE -----------------------------------------------------------------
def test_delete_ok():
    creado = client.post("/users", json={"name": "Para DELETE", "email": "del@device.com"}).json()
    r = client.delete(f"/users/{creado['id']}", headers=AUTH)
    assert r.status_code == 204
    assert client.get(f"/users/{creado['id']}").status_code == 404


def test_delete_sin_api_key():
    creado = client.post("/users", json={"name": "Sin Key", "email": "sinkey@device.com"}).json()
    r = client.delete(f"/users/{creado['id']}")  # sin cabecera
    assert r.status_code == 401


def test_delete_usuario_inexistente():
    assert client.delete("/users/9999", headers=AUTH).status_code == 404
