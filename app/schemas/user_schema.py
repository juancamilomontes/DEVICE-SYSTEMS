"""Schemas Pydantic v2 para el recurso `users`.

Los schemas validan los datos que ENTRAN y SALEN por la API (JSON). Son
distintos del modelo SQLAlchemy (que define la tabla). Aquí hay 4:
- UserCreate:  crear (POST)         -> todos los campos.
- UserUpdate:  reemplazo completo (PUT) -> todos los campos.
- UserPatch:   actualización parcial (PATCH) -> todos opcionales.
- UserResponse: lo que devuelve la API -> incluye id y created_at.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRole(str, Enum):
    """Roles permitidos. Al heredar de `str`, viaja como texto en el JSON."""

    admin = "admin"
    support = "support"
    user = "user"


class UserBase(BaseModel):
    """Campos comunes con validaciones. Los reutilizan Create y Update."""

    name: str = Field(..., min_length=3, description="Nombre, mínimo 3 caracteres")
    email: EmailStr = Field(..., description="Correo válido y único")
    role: UserRole = Field(default=UserRole.user, description="admin, support o user")
    is_active: bool = Field(default=True, description="Usuario activo o no")


class UserCreate(UserBase):
    """Entrada para POST /users (crear)."""

    pass


class UserUpdate(UserBase):
    """Entrada para PUT /users/{id} (reemplazo COMPLETO: todos los campos)."""

    pass


class UserPatch(BaseModel):
    """Entrada para PATCH /users/{id} (actualización PARCIAL).

    Todos los campos opcionales: el cliente envía solo lo que quiere cambiar.
    """

    name: str | None = Field(default=None, min_length=3, description="Nuevo nombre (mín. 3)")
    email: EmailStr | None = Field(default=None, description="Nuevo correo válido")
    role: UserRole | None = Field(default=None, description="Nuevo rol")
    is_active: bool | None = Field(default=None, description="Nuevo estado")


class UserResponse(UserBase):
    """Salida de la API (response_model). Incluye los datos que genera la BD."""

    id: int = Field(..., description="Identificador único (lo asigna la base de datos)")
    created_at: datetime | None = Field(default=None, description="Fecha de creación")

    # from_attributes=True permite crear el schema DIRECTO desde el objeto
    # SQLAlchemy (leyendo user.id, user.name, ...), no solo desde un dict.
    model_config = ConfigDict(from_attributes=True)
