"""Capa de servicios: operaciones CRUD sobre la base de datos.

Cada función recibe la sesión `db` (SQLAlchemy) y hace la consulta o el cambio.
Las rutas solo llaman a estas funciones; si cambia la base de datos, aquí es
donde se toca, no en los endpoints.
"""

from sqlalchemy import asc
from sqlalchemy.orm import Session

from app.models.user_model import User
from app.schemas.user_schema import UserCreate, UserUpdate


# --- Lectura ----------------------------------------------------------------
def get_users(
    db: Session,
    role: str | None = None,
    is_active: bool | None = None,
    order_by: str = "name",
) -> list[User]:
    """Lista usuarios, con filtros opcionales y ordenamiento.

    - role / is_active: filtros opcionales (WHERE).
    - order_by: "name" o "created_at" (ORDER BY).
    """
    query = db.query(User)

    if role is not None:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    # Ordena por fecha de creación si lo piden; por defecto, por nombre.
    columna = User.created_at if order_by == "created_at" else User.name
    query = query.order_by(asc(columna))

    return query.all()


def get_user(db: Session, user_id: int) -> User | None:
    """Busca un usuario por id. Devuelve el objeto o None."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    """Busca un usuario por email (para detectar duplicados)."""
    return db.query(User).filter(User.email == email).first()


# --- Escritura --------------------------------------------------------------
def create_user(db: Session, data: UserCreate) -> User:
    """Crea un usuario nuevo en la base de datos."""
    nuevo = User(
        name=data.name,
        email=data.email,
        role=data.role.value,  # el enum se guarda como texto
        is_active=data.is_active,
    )
    db.add(nuevo)       # lo marca para insertar
    db.commit()         # confirma (INSERT real en la BD)
    db.refresh(nuevo)   # recarga el objeto con el id y created_at generados
    return nuevo


def update_user(db: Session, user: User, data: UserUpdate) -> User:
    """Reemplaza TODOS los campos de un usuario (PUT)."""
    user.name = data.name
    user.email = data.email
    user.role = data.role.value
    user.is_active = data.is_active
    db.commit()
    db.refresh(user)
    return user


def patch_user(db: Session, user: User, changes: dict) -> User:
    """Actualiza SOLO los campos enviados (PATCH)."""
    for campo, valor in changes.items():
        setattr(user, campo, valor)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    """Elimina un usuario de la base de datos."""
    db.delete(user)
    db.commit()
