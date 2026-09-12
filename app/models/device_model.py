"""Modelo SQLAlchemy del dispositivo: tabla `devices`.

Representa los equipos tecnológicos disponibles para préstamo
(laptop, tablet, proyector, cámara, router, monitor, ...).
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Device(Base):
    """Tabla `devices`. Cada fila es un equipo."""

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    # Número de serie: único y obligatorio (no puede repetirse).
    serial_number = Column(String, unique=True, nullable=False, index=True)
    device_type = Column(String, nullable=False)  # laptop, tablet, proyector...
    brand = Column(String, nullable=True)          # opcional
    is_available = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Un dispositivo puede aparecer en muchos préstamos (histórico).
    loans = relationship("Loan", back_populates="device")
