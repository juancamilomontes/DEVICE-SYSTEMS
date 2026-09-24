"""Pruebas de autenticación: registro, login, /auth/me."""


def _reg(client, email="ana@sena.edu.co", password="Password1", role="user", name="Ana Perez"):
    return client.post("/auth/register", json={
        "name": name, "email": email, "password": password, "role": role,
    })


def test_register_ok_sin_password_en_respuesta(client):
    r = _reg(client)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "ana@sena.edu.co"
    assert "hashed_password" not in body  # nunca se expone
    assert "password" not in body


def test_register_password_debil_422(client):
    # "abc" no cumple las reglas (corta, sin mayúscula ni número).
    assert _reg(client, email="debil@sena.edu.co", password="abc").status_code == 422


def test_register_email_duplicado_400(client):
    assert _reg(client, email="dup@sena.edu.co").status_code == 201
    assert _reg(client, email="dup@sena.edu.co").status_code == 400


def test_login_ok_devuelve_token(client):
    _reg(client, email="log@sena.edu.co")
    r = client.post("/auth/login", data={"username": "log@sena.edu.co", "password": "Password1"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_login_password_incorrecta_401(client):
    _reg(client, email="bad@sena.edu.co")
    r = client.post("/auth/login", data={"username": "bad@sena.edu.co", "password": "Otra123X"})
    assert r.status_code == 401


def test_me_con_token(client):
    _reg(client, email="me@sena.edu.co", name="Yo Mismo")
    tok = client.post("/auth/login", data={"username": "me@sena.edu.co", "password": "Password1"}).json()["access_token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    assert r.json()["email"] == "me@sena.edu.co"
    assert "hashed_password" not in r.json()


def test_me_sin_token_401(client):
    assert client.get("/auth/me").status_code == 401


def test_me_token_invalido_401(client):
    assert client.get("/auth/me", headers={"Authorization": "Bearer token-falso"}).status_code == 401
