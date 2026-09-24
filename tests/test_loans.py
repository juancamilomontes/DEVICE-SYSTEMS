"""Pruebas del recurso loans: reglas de negocio, joins, filtros y protección."""


def _device(client, admin_headers, serial="LEN-2024-001", device_type="laptop", name="Laptop Lenovo ThinkPad"):
    return client.post("/devices", json={
        "name": name, "serial_number": serial, "device_type": device_type, "brand": "Lenovo",
    }, headers=admin_headers).json()


def _user_id(client, admin_headers, email="user@device.com"):
    users = client.get("/users", headers=admin_headers).json()
    return next(u["id"] for u in users if u["email"] == email)


def test_crear_prestamo_sin_token_401(client, admin_headers):
    d = _device(client, admin_headers, serial="NT-1")
    uid = _user_id(client, admin_headers, "admin@device.com")
    assert client.post("/loans", json={"user_id": uid, "device_id": d["id"]}).status_code == 401


def test_crear_prestamo_ok_y_no_disponible(client, admin_headers, user_headers):
    d = _device(client, admin_headers, serial="OK-1")
    uid = _user_id(client, admin_headers)
    r = client.post("/loans", json={"user_id": uid, "device_id": d["id"]}, headers=user_headers)
    assert r.status_code == 201
    assert r.json()["user"]["email"] == "user@device.com"
    assert r.json()["device"]["serial_number"] == "OK-1"
    # el dispositivo quedó no disponible
    assert client.get(f"/devices/{d['id']}").json()["is_available"] is False


def test_prestar_no_disponible_409(client, admin_headers, user_headers):
    d = _device(client, admin_headers, serial="OCU-1")
    uid = _user_id(client, admin_headers)
    client.post("/loans", json={"user_id": uid, "device_id": d["id"]}, headers=user_headers)
    r = client.post("/loans", json={"user_id": uid, "device_id": d["id"]}, headers=user_headers)
    assert r.status_code == 409


def test_prestar_usuario_o_device_inexistente_404(client, admin_headers, user_headers):
    d = _device(client, admin_headers, serial="X-1")
    assert client.post("/loans", json={"user_id": 9999, "device_id": d["id"]}, headers=user_headers).status_code == 404
    uid = _user_id(client, admin_headers)
    assert client.post("/loans", json={"user_id": uid, "device_id": 9999}, headers=user_headers).status_code == 404


def test_details_requiere_admin_o_support(client, admin_headers, user_headers):
    d = _device(client, admin_headers, serial="DET-1")
    uid = _user_id(client, admin_headers)
    client.post("/loans", json={"user_id": uid, "device_id": d["id"]}, headers=user_headers)
    # usuario normal -> 403
    assert client.get("/loans/details", headers=user_headers).status_code == 403
    # admin -> 200 con join
    det = client.get("/loans/details", headers=admin_headers)
    assert det.status_code == 200 and len(det.json()) == 1


def test_filtros_por_estado_y_tipo(client, admin_headers, user_headers):
    d1 = _device(client, admin_headers, serial="L-1", device_type="laptop")
    d2 = _device(client, admin_headers, serial="T-1", device_type="tablet")
    uid = _user_id(client, admin_headers)
    client.post("/loans", json={"user_id": uid, "device_id": d1["id"]}, headers=user_headers)
    client.post("/loans", json={"user_id": uid, "device_id": d2["id"]}, headers=user_headers)
    assert len(client.get("/loans", params={"status": "active"}).json()) == 2
    assert len(client.get("/loans", params={"device_type": "tablet"}).json()) == 1


def test_devolver_requiere_rol_y_libera_dispositivo(client, admin_headers, user_headers):
    d = _device(client, admin_headers, serial="RET-1")
    uid = _user_id(client, admin_headers)
    loan = client.post("/loans", json={"user_id": uid, "device_id": d["id"]}, headers=user_headers).json()
    # usuario normal no puede devolver -> 403
    assert client.patch(f"/loans/{loan['loan_id']}/return", headers=user_headers).status_code == 403
    # admin sí -> 200
    r = client.patch(f"/loans/{loan['loan_id']}/return", headers=admin_headers)
    assert r.status_code == 200 and r.json()["status"] == "returned"
    assert client.get(f"/devices/{d['id']}").json()["is_available"] is True
    # devolver otra vez -> 409
    assert client.patch(f"/loans/{loan['loan_id']}/return", headers=admin_headers).status_code == 409


def test_prestamos_por_usuario_y_dispositivo(client, admin_headers, user_headers):
    d = _device(client, admin_headers, serial="HIST-1")
    uid = _user_id(client, admin_headers)
    client.post("/loans", json={"user_id": uid, "device_id": d["id"]}, headers=user_headers)
    assert len(client.get(f"/users/{uid}/loans", headers=admin_headers).json()) == 1
    assert len(client.get(f"/devices/{d['id']}/loans").json()) == 1
