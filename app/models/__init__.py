"""Registra todos los modelos al importar el paquete `app.models`.

Importar los tres módulos aquí asegura que SQLAlchemy conozca User, Device y
Loan (necesario para que las relaciones por nombre y Alembic funcionen).
"""

from app.models.device_model import Device
from app.models.loan_model import Loan
from app.models.user_model import User

__all__ = ["User", "Device", "Loan"]
