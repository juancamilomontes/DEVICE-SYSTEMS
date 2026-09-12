"""Pruebas del recurso users (CRUD sobre base de datos)."""

AUTH = {"X-API-Key": "device-systems-2026"}


def crear(client, name="Test User", email="test@device.com", role="user"):
    return client.post("/users", json={"name": name, "email": email, "role": role})


def test_crear_usuario_ok(client):
    r = crear(client)
    assert r.status_code == 201
    assert "created_at" in r.json()


def test_crear_email_duplicado(client):
    assert crear(client, email="dup@device.com").status_code == 201
    assert crear(client, email="dup@device.com").status_code == 400


def test_crear_nombre_corto(client):
    assert client.post("/users", json={"name": "ab", "email": "x@device.com"}).status_code == 422


def test_crear_email_invalido(client):
    assert client.post("/users", json={"name": "Valido", "email": "malo"}).status_code == 422


def test_listar_y_cabeceras(client):
    crear(client, email="a@device.com")
    r = client.get("/users")
    assert r.status_code == 200
    assert r.headers["X-App-Name"] == "device_systems"
    assert r.headers["X-API-Version"] == "4.0"


def test_obtener_inexistente(client):
    assert client.get("/users/9999").status_code == 404


def test_put_y_patch(client):
    uid = crear(client, email="pp@device.com").json()["id"]
    r = client.put(f"/users/{uid}", json={"name": "Edit PUT", "email": "pp@device.com", "role": "admin", "is_active": False})
    assert r.status_code == 200 and r.json()["role"] == "admin"
    r = client.patch(f"/users/{uid}", json={"role": "support"})
    assert r.status_code == 200 and r.json()["role"] == "support"


def test_patch_vacio_400(client):
    uid = crear(client, email="v@device.com").json()["id"]
    assert client.patch(f"/users/{uid}", json={}).status_code == 400


def test_delete(client):
    uid = crear(client, email="del@device.com").json()["id"]
    assert client.delete(f"/users/{uid}", headers=AUTH).status_code == 204
    assert client.delete(f"/users/{uid}", headers=AUTH).status_code == 404
    # sin API key -> 401
    uid2 = crear(client, email="del2@device.com").json()["id"]
    assert client.delete(f"/users/{uid2}").status_code == 401


def test_info(client):
    assert client.get("/info").json()["version"] == "4.0.0"
