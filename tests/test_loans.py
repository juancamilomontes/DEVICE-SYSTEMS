"""Pruebas del recurso loans: reglas de negocio, joins y filtros.

Cubre los escenarios de la Fase 13 de la guía.
"""


def _usuario(client, email="ana@sena.edu.co", name="Ana Perez"):
    return client.post("/users", json={"name": name, "email": email, "role": "user"}).json()


def _dispositivo(client, serial="LEN-2024-001", device_type="laptop", name="Laptop Lenovo ThinkPad"):
    return client.post("/devices", json={
        "name": name, "serial_number": serial, "device_type": device_type, "brand": "Lenovo",
    }).json()


def test_crear_prestamo_ok_y_marca_no_disponible(client):
    u = _usuario(client)
    d = _dispositivo(client)
    r = client.post("/loans", json={"user_id": u["id"], "device_id": d["id"]})
    assert r.status_code == 201
    body = r.json()
    # La respuesta trae info relacionada (join): usuario y dispositivo.
    assert body["user"]["email"] == "ana@sena.edu.co"
    assert body["device"]["serial_number"] == "LEN-2024-001"
    assert body["status"] == "active"
    # El dispositivo quedó NO disponible.
    assert client.get(f"/devices/{d['id']}").json()["is_available"] is False


def test_prestar_dispositivo_no_disponible_409(client):
    u = _usuario(client)
    d = _dispositivo(client, serial="OCU-1")
    client.post("/loans", json={"user_id": u["id"], "device_id": d["id"]})  # ya prestado
    r = client.post("/loans", json={"user_id": u["id"], "device_id": d["id"]})
    assert r.status_code == 409


def test_prestar_usuario_o_dispositivo_inexistente_404(client):
    d = _dispositivo(client, serial="X-1")
    assert client.post("/loans", json={"user_id": 999, "device_id": d["id"]}).status_code == 404
    u = _usuario(client, email="b@sena.edu.co")
    assert client.post("/loans", json={"user_id": u["id"], "device_id": 999}).status_code == 404


def test_listar_detalle_y_filtros(client):
    u = _usuario(client, email="filtro@sena.edu.co")
    d1 = _dispositivo(client, serial="L-1", device_type="laptop")
    d2 = _dispositivo(client, serial="T-1", device_type="tablet")
    client.post("/loans", json={"user_id": u["id"], "device_id": d1["id"]})
    client.post("/loans", json={"user_id": u["id"], "device_id": d2["id"]})

    # /loans/details con join
    det = client.get("/loans/details")
    assert det.status_code == 200 and len(det.json()) == 2

    # filtro por estado
    assert len(client.get("/loans", params={"status": "active"}).json()) == 2
    # filtro por correo del usuario (join)
    assert len(client.get("/loans", params={"user_email": "filtro@sena.edu.co"}).json()) == 2
    # filtro por tipo de dispositivo (join)
    assert len(client.get("/loans", params={"device_type": "tablet"}).json()) == 1


def test_devolver_y_disponibilidad(client):
    u = _usuario(client, email="dev@sena.edu.co")
    d = _dispositivo(client, serial="RET-1")
    loan = client.post("/loans", json={"user_id": u["id"], "device_id": d["id"]}).json()

    r = client.patch(f"/loans/{loan['loan_id']}/return")
    assert r.status_code == 200
    assert r.json()["status"] == "returned"
    assert r.json()["return_date"] is not None
    # El dispositivo vuelve a estar disponible.
    assert client.get(f"/devices/{d['id']}").json()["is_available"] is True
    # Devolver otra vez -> 409
    assert client.patch(f"/loans/{loan['loan_id']}/return").status_code == 409


def test_devolver_inexistente_404(client):
    assert client.patch("/loans/9999/return").status_code == 404


def test_prestamos_por_usuario_y_por_dispositivo(client):
    u = _usuario(client, email="hist@sena.edu.co")
    d = _dispositivo(client, serial="HIST-1")
    loan = client.post("/loans", json={"user_id": u["id"], "device_id": d["id"]}).json()
    client.patch(f"/loans/{loan['loan_id']}/return")  # devuelto -> historial

    # préstamos del usuario
    ul = client.get(f"/users/{u['id']}/loans")
    assert ul.status_code == 200 and len(ul.json()) == 1
    # historial del dispositivo
    dl = client.get(f"/devices/{d['id']}/loans")
    assert dl.status_code == 200 and len(dl.json()) == 1
    assert dl.json()[0]["device"]["serial_number"] == "HIST-1"
