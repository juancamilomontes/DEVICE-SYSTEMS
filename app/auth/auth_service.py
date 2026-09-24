"""Lógica de negocio de autenticación: registrar y autenticar usuarios."""

from sqlalchemy.orm import Session

from app.auth.security import get_password_hash, verify_password
from app.models.user_model import User
from app.schemas.auth_schema import UserRegister


def register_user(db: Session, data: UserRegister) -> User:
    """Crea un usuario nuevo guardando SOLO el hash de la contraseña."""
    nuevo = User(
        name=data.name,
        email=data.email,
        hashed_password=get_password_hash(data.password),  # nunca texto plano
        role=data.role.value,
        is_active=True,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Devuelve el usuario si el correo existe y la contraseña coincide; si no, None."""
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
