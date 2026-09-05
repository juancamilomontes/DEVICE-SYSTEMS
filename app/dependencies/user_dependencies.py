"""Dependencias reutilizables con `Depends()`.

FastAPI ejecuta estas funciones ANTES de la función del endpoint e inyecta su
resultado como parámetro. Así se evita repetir la misma lógica (buscar un
usuario, validar una cabecera, etc.) en cada ruta.
"""

from fastapi import Depends, Header, HTTPException, status

from app.services.user_service import UserService


def get_user_service() -> UserService:
    """Provee una instancia del servicio de usuarios.

    Al inyectarla con Depends(), las rutas no crean el servicio a mano y se
    podría cambiar por otra implementación sin tocar los endpoints.
    """
    return UserService()


def get_user_or_404(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> dict:
    """Obtiene un usuario por id o lanza 404 si no existe.

    Es la dependencia estrella: se reutiliza en GET/{id}, PUT, PATCH y DELETE.
    `user_id` se toma del path de la ruta que la use.
    """
    user = service.get_user(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )
    return user


def get_api_settings() -> dict:
    """Configuración general de la API (metadatos que se pueden inyectar)."""
    return {
        "app_name": "device_systems",
        "version": "2.0.0",
        "author": "Juan Camilo Montes",
    }


# Clave esperada para operaciones protegidas (autenticación básica simulada).
API_KEY = "device-systems-2026"


def verify_api_key(
    x_api_key: str | None = Header(
        default=None,
        description="Clave de API requerida para operaciones protegidas (ej. DELETE)",
    ),
) -> None:
    """Simula autenticación básica mediante una cabecera HTTP.

    Si la cabecera `X-API-Key` no coincide con la clave esperada, corta la
    petición con 401. Se aplica, por ejemplo, al endpoint DELETE.
    """
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida o ausente",
        )
