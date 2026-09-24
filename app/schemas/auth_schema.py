"""Schemas de autenticación con Pydantic v2.

Aplica validación avanzada: Field() para metadata/restricciones y
field_validator para exigir una contraseña segura.
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.auth.security import validate_password_strength
from app.schemas.user_schema import UserRole


class UserRegister(BaseModel):
    """Datos para registrar un usuario (POST /auth/register)."""

    name: str = Field(..., min_length=3, description="Nombre, mínimo 3 caracteres")
    email: EmailStr = Field(..., description="Correo válido y único")
    password: str = Field(..., min_length=8, description="Contraseña segura")
    role: UserRole = Field(default=UserRole.user, description="admin, support o user")

    @field_validator("password")
    @classmethod
    def _password_segura(cls, v: str) -> str:
        # Reglas: 8+ caracteres, mayúscula, minúscula, número y sin espacios.
        return validate_password_strength(v)


class UserLogin(BaseModel):
    """Datos para iniciar sesión (documentación; el login usa formulario OAuth2)."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """Respuesta del login: el token JWT y su tipo."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Datos que viajan dentro del token (identidad del usuario)."""

    email: str | None = None

    model_config = ConfigDict(from_attributes=True)
