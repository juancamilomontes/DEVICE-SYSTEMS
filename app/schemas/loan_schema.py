"""Schemas Pydantic del recurso `loans`.

Incluye LoanDetailResponse, que muestra el préstamo con los datos relacionados
del usuario y del dispositivo (resultado de las consultas con joins).
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class LoanStatus(str, Enum):
    """Estados posibles de un préstamo."""

    active = "active"
    returned = "returned"
    overdue = "overdue"


class LoanCreate(BaseModel):
    """Entrada para POST /loans. Solo se indica a quién y qué se presta."""

    user_id: int = Field(..., description="ID del usuario que recibe el préstamo")
    device_id: int = Field(..., description="ID del dispositivo prestado")


class LoanUpdate(BaseModel):
    """Entrada opcional para actualizar un préstamo (estado / fecha de devolución)."""

    status: LoanStatus | None = None
    return_date: datetime | None = None


class LoanResponse(BaseModel):
    """Salida básica de un préstamo (con los ids relacionados)."""

    id: int
    user_id: int
    device_id: int
    loan_date: datetime | None = None
    return_date: datetime | None = None
    status: str

    model_config = ConfigDict(from_attributes=True)


# --- Datos resumidos para las respuestas con joins -------------------------
class UserBrief(BaseModel):
    """Datos básicos del usuario dentro de un préstamo detallado."""

    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class DeviceBrief(BaseModel):
    """Datos básicos del dispositivo dentro de un préstamo detallado."""

    id: int
    name: str
    serial_number: str
    device_type: str

    model_config = ConfigDict(from_attributes=True)


class LoanDetailResponse(BaseModel):
    """Préstamo con información relacionada de usuario y dispositivo (joins)."""

    loan_id: int
    status: str
    loan_date: datetime | None = None
    return_date: datetime | None = None
    user: UserBrief
    device: DeviceBrief

    model_config = ConfigDict(from_attributes=True)
