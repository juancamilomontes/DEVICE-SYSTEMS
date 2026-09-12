"""Modelo SQLAlchemy del usuario: representa la TABLA `users` en la base de datos.

OJO: esto NO es lo mismo que el schema Pydantic.
- Este modelo (SQLAlchemy) describe cómo se GUARDA el usuario en la base de datos
  (columnas, tipos SQL, restricciones como unique/nullable).
- El schema Pydantic (user_schema.py) describe cómo ENTRAN y SALEN los datos por
  la API (validación de JSON).
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database.connection import Base


class User(Base):
    """Tabla `users`. Cada instancia = una fila."""

    __tablename__ = "users"

    # Clave primaria autoincremental. index=True acelera las búsquedas por id.
    id = Column(Integer, primary_key=True, index=True)

    # Obligatorio: nullable=False significa que no puede quedar vacío.
    name = Column(String, nullable=False)

    # Único y obligatorio: unique=True crea una restricción en la base de datos
    # que impide dos usuarios con el mismo correo.
    email = Column(String, unique=True, nullable=False, index=True)

    # Obligatorio. Los valores permitidos (admin/support/user) los valida Pydantic.
    role = Column(String, nullable=False, default="user")

    # Booleano con valor por defecto True.
    is_active = Column(Boolean, nullable=False, default=True)

    # Fecha de creación: se rellena sola con la hora actual (UTC) al insertar.
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relación 1-a-muchos: un usuario puede tener MUCHOS préstamos.
    # back_populates enlaza con Loan.user (los dos lados quedan sincronizados).
    loans = relationship("Loan", back_populates="user")
