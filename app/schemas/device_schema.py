"""Schemas Pydantic del recurso `devices` (entrada/salida de la API)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DeviceBase(BaseModel):
    """Campos comunes con validaciones."""

    name: str = Field(..., min_length=3, description="Nombre del dispositivo")
    serial_number: str = Field(..., min_length=3, description="Número de serie único")
    device_type: str = Field(..., min_length=3, description="laptop, tablet, proyector, camara, router, monitor...")
    brand: str | None = Field(default=None, description="Marca (opcional)")
    is_available: bool = Field(default=True, description="¿Disponible para préstamo?")


class DeviceCreate(DeviceBase):
    """Entrada para POST /devices."""

    pass


class DeviceUpdate(DeviceBase):
    """Entrada para PUT /devices/{id} (reemplazo completo)."""

    pass


class DevicePatch(BaseModel):
    """Entrada para PATCH /devices/{id} (parcial: todo opcional)."""

    name: str | None = Field(default=None, min_length=3)
    serial_number: str | None = Field(default=None, min_length=3)
    device_type: str | None = Field(default=None, min_length=3)
    brand: str | None = None
    is_available: bool | None = None


class DeviceResponse(DeviceBase):
    """Salida de la API."""

    id: int
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
