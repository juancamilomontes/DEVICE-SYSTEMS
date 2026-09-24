"""Dependencias reutilizables con `Depends()`.

FastAPI ejecuta estas funciones ANTES del endpoint e inyecta su resultado. Así
se evita repetir la misma lógica (buscar un usuario, etc.).
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.database_dependency import get_db
from app.models.user_model import User
from app.services import user_service


def get_user_or_404(
    user_id: int,
    db: Session = Depends(get_db),
) -> User:
    """Obtiene un usuario por id desde la base de datos, o lanza 404.

    Se reutiliza en GET/{id}, PUT, PATCH y DELETE. `user_id` se toma del path.
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
        "version": "5.0.0",
        "author": "Juan Camilo Montes",
    }
