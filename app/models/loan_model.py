"""Modelo SQLAlchemy del préstamo: tabla `loans`.

Es la tabla "puente" que relaciona un usuario con un dispositivo. Cada préstamo
pertenece a UN usuario y a UN dispositivo (integridad referencial con ForeignKey).
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Loan(Base):
    """Tabla `loans`. Registra el préstamo de un dispositivo a un usuario."""

    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)

    # Claves foráneas: garantizan que el préstamo apunte a filas que existen.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)

    loan_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    return_date = Column(DateTime, nullable=True)  # se llena al devolver
    status = Column(String, nullable=False, default="active")  # active/returned/overdue

    # Lado "muchos-a-uno": cada préstamo tiene un usuario y un dispositivo.
    # back_populates enlaza con User.loans y Device.loans.
    user = relationship("User", back_populates="loans")
    device = relationship("Device", back_populates="loans")
