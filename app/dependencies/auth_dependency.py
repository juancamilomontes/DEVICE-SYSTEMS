"""Dependencias de autenticación y autorización (protección de rutas).

- get_current_user: exige un token JWT válido y devuelve el usuario.
- get_current_active_user: además, que el usuario esté activo.
- require_admin / require_admin_or_support: exigen un rol concreto (403 si no).
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.dependencies.database_dependency import get_db
from app.models.user_model import User

# Esquema OAuth2: Swagger mostrará el botón "Authorize"; el token se lee del
# header Authorization: Bearer <token>. tokenUrl apunta al endpoint de login.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Excepción reutilizable para credenciales inválidas.
_credenciales_invalidas = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No se pudo validar el token",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Obtiene el usuario a partir del token JWT. 401 si el token es inválido."""
    payload = decode_access_token(token)
    if payload is None:
        raise _credenciales_invalidas

    email = payload.get("sub")
    if email is None:
        raise _credenciales_invalidas

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise _credenciales_invalidas
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Exige que el usuario esté activo."""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")
    return current_user


def require_roles(*roles: str):
    """Crea una dependencia que exige que el usuario tenga uno de los roles dados."""

    def _checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para esta operación",
            )
        return current_user

    return _checker


# Dependencias concretas según la tabla de protección de la guía.
require_admin = require_roles("admin")
require_admin_or_support = require_roles("admin", "support")
