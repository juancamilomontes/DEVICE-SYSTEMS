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


def _nuevo(email="nuevo@device.com", role="user"):
    return {"name": "Nuevo Usuario", "email": email, "password": "Password1", "role": role}


def test_post_users_admin_201(client, admin_headers):
    r = client.post("/users", json=_nuevo(), headers=admin_headers)
    assert r.status_code == 201
    assert "hashed_password" not in r.json()  # nunca se expone


def test_post_users_sin_token_401(client):
    assert client.post("/users", json=_nuevo(email="a@device.com")).status_code == 401


def test_post_users_usuario_normal_403(client, user_headers):
    assert client.post("/users", json=_nuevo(email="b@device.com"), headers=user_headers).status_code == 403


def test_post_users_email_duplicado_400(client, admin_headers):
    assert client.post("/users", json=_nuevo(email="dup@device.com"), headers=admin_headers).status_code == 201
    assert client.post("/users", json=_nuevo(email="dup@device.com"), headers=admin_headers).status_code == 400


def test_post_users_password_debil_422(client, admin_headers):
    payload = {"name": "Debil", "email": "d@device.com", "password": "abc", "role": "user"}
    assert client.post("/users", json=payload, headers=admin_headers).status_code == 422


def test_info(client):
    assert client.get("/info").json()["version"] == "5.0.0"
