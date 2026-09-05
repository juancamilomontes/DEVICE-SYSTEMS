"""Capa de servicios: lógica de negocio del recurso `users`.

Aquí vive TODO lo que hace la API con los usuarios (buscar, filtrar, crear,
reemplazar, actualizar, eliminar). Las rutas solo llaman a estos métodos; así,
si mañana se cambia la lista en memoria por una base de datos real, solo se
toca este archivo y no los endpoints.
"""

from app.data.users_db import users_db
from app.schemas.user_schema import UserCreate


class UserService:
    """Servicio que opera sobre la "base de datos" en memoria.

    Recibe la lista como dependencia (por defecto `users_db`), lo que facilita
    inyectarla y probarla.
    """

    def __init__(self, db: list[dict] = users_db):
        self._db = db

    # --- Lectura ------------------------------------------------------------
    def list_users(self, role: str | None = None, is_active: bool | None = None) -> list[dict]:
        """Devuelve todos los usuarios, con filtros opcionales por rol y estado."""
        resultado = self._db
        if role is not None:
            resultado = [u for u in resultado if u["role"] == role]
        if is_active is not None:
            resultado = [u for u in resultado if u["is_active"] == is_active]
        return resultado

    def get_user(self, user_id: int) -> dict | None:
        """Busca un usuario por id. Devuelve el dict o None si no existe."""
        return next((u for u in self._db if u["id"] == user_id), None)

    def email_exists(self, email: str, exclude_id: int | None = None) -> bool:
        """Indica si un correo ya está en uso.

        `exclude_id` permite ignorar a un usuario concreto (útil al actualizar:
        el propio usuario puede conservar su correo sin marcarlo como duplicado).
        """
        email = email.lower()
        return any(
            u["email"].lower() == email and u["id"] != exclude_id
            for u in self._db
        )

    # --- Escritura ----------------------------------------------------------
    def _next_id(self) -> int:
        """Calcula el siguiente id como el máximo actual + 1."""
        return max((u["id"] for u in self._db), default=0) + 1

    def create_user(self, data: UserCreate) -> dict:
        """Crea un usuario nuevo y lo agrega a la base."""
        nuevo = data.model_dump(mode="json")  # role/email quedan como texto
        nuevo["id"] = self._next_id()
        self._db.append(nuevo)
        return nuevo

    def replace_user(self, user: dict, data: UserCreate) -> dict:
        """Reemplaza TODOS los campos de un usuario existente (PUT)."""
        user.update(data.model_dump(mode="json"))  # el id se conserva
        return user

    def apply_changes(self, user: dict, changes: dict) -> dict:
        """Actualiza solo los campos enviados (PATCH)."""
        user.update(changes)
        return user

    def delete_user(self, user: dict) -> None:
        """Elimina un usuario de la base."""
        self._db.remove(user)
