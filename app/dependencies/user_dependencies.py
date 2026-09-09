"""Dependencias reutilizables con `Depends()`.

FastAPI ejecuta estas funciones ANTES del endpoint e inyecta su resultado. Así
se evita repetir la misma lógica (buscar un usuario, validar una cabecera).
"""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.database_dependency import get_db
from app.models.user_model import User
from app.services import user_service


def get_user_or_404(
    user_id: int,
    db: Session = Depends(get_db),
) -> User:
    """Obtiene un usuario por id desde la base de datos, o lanza 404.

    Es la dependencia estrella: se reutiliza en GET/{id}, PUT, PATCH y DELETE.
    `user_id` se toma del path; `db` es la sesión inyectada por get_db.
    """
    user = user_service.get_user(db, user_id)
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
        "version": "3.0.0",
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

    Si `X-API-Key` no coincide con la clave esperada, corta con 401.
    """
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida o ausente",
        )
