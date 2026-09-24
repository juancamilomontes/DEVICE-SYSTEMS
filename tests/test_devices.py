"""Pruebas del recurso devices con protección por rol."""


def _payload(serial="LEN-001", name="Laptop Lenovo", device_type="laptop", brand="Lenovo"):
    return {"name": name, "serial_number": serial, "device_type": device_type, "brand": brand}


def test_crear_sin_token_401(client):
    assert client.post("/devices", json=_payload()).status_code == 401


def test_crear_usuario_normal_403(client, user_headers):
    assert client.post("/devices", json=_payload(), headers=user_headers).status_code == 403


def test_crear_admin_201(client, admin_headers):
    r = client.post("/devices", json=_payload(serial="ADM-1"), headers=admin_headers)
    assert r.status_code == 201
    assert r.json()["is_available"] is True


def test_crear_support_201(client, support_headers):
    r = client.post("/devices", json=_payload(serial="SUP-1"), headers=support_headers)
    assert r.status_code == 201


def test_serial_duplicado_400(client, admin_headers):
    assert client.post("/devices", json=_payload(serial="DUP-1"), headers=admin_headers).status_code == 201
    assert client.post("/devices", json=_payload(serial="DUP-1", name="Otro"), headers=admin_headers).status_code == 400


def test_nombre_corto_422(client, admin_headers):
    r = client.post("/devices", json={"name": "ab", "serial_number": "S1", "device_type": "laptop"}, headers=admin_headers)
    assert r.status_code == 422


def test_listar_y_filtros_publico(client, admin_headers):
    client.post("/devices", json=_payload(serial="F-1", device_type="laptop", brand="Lenovo"), headers=admin_headers)
    client.post("/devices", json=_payload(serial="F-2", name="Tablet", device_type="tablet", brand="Samsung"), headers=admin_headers)
    # GET /devices es público (no está en la tabla de protección)
    assert len(client.get("/devices").json()) == 2
    assert len(client.get("/devices", params={"device_type": "laptop"}).json()) == 1
    assert len(client.get("/devices", params={"brand": "lenovo"}).json()) == 1
    assert len(client.get("/devices", params={"search": "tablet"}).json()) == 1


def test_eliminar_admin_ok_y_support_no(client, admin_headers, support_headers):
    did = client.post("/devices", json=_payload(serial="DEL-1"), headers=admin_headers).json()["id"]
    # support NO puede eliminar (solo admin) -> 403
    assert client.delete(f"/devices/{did}", headers=support_headers).status_code == 403
    # admin sí -> 204
    assert client.delete(f"/devices/{did}", headers=admin_headers).status_code == 204
