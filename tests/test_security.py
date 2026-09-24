"""Pruebas de la capa de seguridad: middleware, CORS y rate limiting."""

from app.middlewares.rate_limit import limiter


def test_middleware_cabeceras(client):
    r = client.get("/estado")
    assert r.headers["X-App-Name"] == "device_systems"
    assert "X-Process-Time" in r.headers
    assert "X-Request-ID" in r.headers


def test_cors_origen_permitido(client):
    r = client.get("/estado", headers={"Origin": "http://localhost:5173"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert r.headers.get("access-control-allow-credentials") == "true"


def test_security_status(client):
    r = client.get("/security/status")
    assert r.status_code == 200
    assert r.json()["rate_limiting"] is True


def test_rate_limiting_register(client):
    """Con el limiter activo, el registro (3/min) devuelve 429 al superarse."""
    limiter.enabled = True
    try:
        codigos = []
        for i in range(4):
            r = client.post("/auth/register", json={
                "name": f"User {i}", "email": f"rl{i}@device.com", "password": "Password1", "role": "user",
            })
            codigos.append(r.status_code)
        assert 429 in codigos  # al menos una petición fue bloqueada
    finally:
        limiter.enabled = False
