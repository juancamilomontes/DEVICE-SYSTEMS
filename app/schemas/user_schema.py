"""Modelos Pydantic v2 para el recurso `users` de device_systems.

Aquí se definen:
- El enum de roles permitidos.
- El modelo base con las validaciones compartidas.
- El modelo de entrada (lo que envía el cliente al crear un usuario).
- El modelo de respuesta (lo que la API devuelve, estandarizado).
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRole(str, Enum):
    """Roles permitidos en el sistema. Al heredar de `str`, el valor viaja
    como texto ("admin", "support", "user") en el JSON y en la URL."""

    admin = "admin"
    support = "support"
    user = "user"


class UserBase(BaseModel):
    """Campos comunes con sus validaciones. Los demás modelos heredan de aquí."""

    # name: obligatorio (...) y mínimo 3 caracteres.
    name: str = Field(..., min_length=3, description="Nombre del usuario, mínimo 3 caracteres")
    # email: EmailStr valida el formato del correo automáticamente.
    email: EmailStr = Field(..., description="Correo electrónico válido y único")
    # role: solo admite los valores del enum; por defecto 'user'.
    role: UserRole = Field(default=UserRole.user, description="Rol: admin, support o user")
    # is_active: booleano; por defecto True.
    is_active: bool = Field(default=True, description="Indica si el usuario está activo")


class UserCreate(UserBase):
    """Modelo de ENTRADA para POST /users.

    El cliente NO envía el `id` (lo asigna el servidor), por eso este modelo
    solo tiene los campos de `UserBase`.
    """

    pass


class UserResponse(UserBase):
    """Modelo de SALIDA (response_model).

    Estandariza lo que la API devuelve e incluye el `id` generado por el
    servidor. Al declararlo como response_model, FastAPI filtra cualquier
    campo extra que no esté aquí (así se ocultan datos no necesarios).
    """

    id: int = Field(..., description="Identificador único generado por el servidor")

    # Permite construir el modelo a partir de objetos/atributos, no solo dicts.
    model_config = ConfigDict(from_attributes=True)
