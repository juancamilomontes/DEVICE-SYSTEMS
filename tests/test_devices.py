"""Pruebas del recurso devices (CRUD + filtros + búsqueda)."""

AUTH = {"X-API-Key": "device-systems-2026"}


def crear(client, name="Laptop Lenovo", serial="LEN-001", device_type="laptop", brand="Lenovo"):
    return client.post("/devices", json={
        "name": name, "serial_number": serial, "device_type": device_type, "brand": brand,
    })


def test_crear_dispositivo_ok(client):
    r = crear(client)
    assert r.status_code == 201
    body = r.json()
    assert body["is_available"] is True
    assert "created_at" in body


def test_serial_duplicado_400(client):
    assert crear(client, serial="DUP-1").status_code == 201
    assert crear(client, serial="DUP-1", name="Otro").status_code == 400


def test_nombre_corto_422(client):
    assert client.post("/devices", json={"name": "ab", "serial_number": "S1", "device_type": "laptop"}).status_code == 422


def test_obtener_y_404(client):
    did = crear(client, serial="GET-1").json()["id"]
    assert client.get(f"/devices/{did}").status_code == 200
    assert client.get("/devices/9999").status_code == 404


def test_filtros(client):
    crear(client, name="Laptop A", serial="F-1", device_type="laptop", brand="Lenovo")
    crear(client, name="Tablet B", serial="F-2", device_type="tablet", brand="Samsung")
    assert len(client.get("/devices", params={"device_type": "laptop"}).json()) == 1
    assert len(client.get("/devices", params={"brand": "lenovo"}).json()) == 1  # ilike
    assert len(client.get("/devices", params={"search": "tablet"}).json()) == 1
    assert len(client.get("/devices", params={"is_available": "true"}).json()) == 2


def test_put_patch_delete(client):
    did = crear(client, serial="UP-1").json()["id"]
    r = client.put(f"/devices/{did}", json={"name": "Laptop Nueva", "serial_number": "UP-1", "device_type": "laptop", "brand": "HP", "is_available": True})
    assert r.status_code == 200 and r.json()["brand"] == "HP"
    r = client.patch(f"/devices/{did}", json={"is_available": False})
    assert r.status_code == 200 and r.json()["is_available"] is False
    assert client.patch(f"/devices/{did}", json={}).status_code == 400
    assert client.delete(f"/devices/{did}", headers=AUTH).status_code == 204
    assert client.get(f"/devices/{did}").status_code == 404
