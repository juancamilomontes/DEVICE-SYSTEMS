"""Pruebas del recurso users con protección por token/rol."""


def test_listar_sin_token_401(client):
    assert client.get("/users").status_code == 401


def test_listar_con_token(client, user_headers):
    r = client.get("/users", headers=user_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_obtener_por_id(client, admin_headers):
    # admin ya existe (lo creó el fixture); lo listamos y consultamos por id
    users = client.get("/users", headers=admin_headers).json()
    uid = users[0]["id"]
    assert client.get(f"/users/{uid}", headers=admin_headers).status_code == 200


def test_obtener_inexistente_404(client, admin_headers):
    assert client.get("/users/9999", headers=admin_headers).status_code == 404


def test_admin_puede_editar(client, admin_headers):
    uid = client.get("/users", headers=admin_headers).json()[0]["id"]
    r = client.patch(f"/users/{uid}", json={"role": "support"}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["role"] == "support"


def test_usuario_normal_no_puede_editar_403(client, user_headers):
    uid = client.get("/users", headers=user_headers).json()[0]["id"]
    r = client.patch(f"/users/{uid}", json={"role": "admin"}, headers=user_headers)
    assert r.status_code == 403


def test_usuario_normal_no_puede_eliminar_403(client, user_headers):
    uid = client.get("/users", headers=user_headers).json()[0]["id"]
    assert client.delete(f"/users/{uid}", headers=user_headers).status_code == 403


def test_admin_puede_eliminar(client, admin_headers, make_headers):
    otro = make_headers("otro@device.com", role="user")  # crea otro usuario
    # buscar su id
    users = client.get("/users", headers=admin_headers).json()
    uid = next(u["id"] for u in users if u["email"] == "otro@device.com")
    assert client.delete(f"/users/{uid}", headers=admin_headers).status_code == 204


def test_info(client):
    assert client.get("/info").json()["version"] == "5.0.0"
