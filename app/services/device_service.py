"""Lógica de negocio del recurso `devices` (CRUD + filtros + búsqueda)."""

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.device_model import Device
from app.schemas.device_schema import DeviceCreate, DeviceUpdate


def get_devices(
    db: Session,
    device_type: str | None = None,
    is_available: bool | None = None,
    brand: str | None = None,
    search: str | None = None,
) -> list[Device]:
    """Lista dispositivos con filtros opcionales y búsqueda por texto."""
    query = db.query(Device)

    if device_type is not None:
        query = query.filter(Device.device_type == device_type)
    if is_available is not None:
        query = query.filter(Device.is_available == is_available)
    if brand is not None:
        # ilike = LIKE sin distinguir mayúsculas/minúsculas.
        query = query.filter(Device.brand.ilike(f"%{brand}%"))
    if search is not None:
        # Busca el texto en el nombre O en el número de serie.
        patron = f"%{search}%"
        query = query.filter(or_(Device.name.ilike(patron), Device.serial_number.ilike(patron)))

    return query.order_by(Device.name).all()


def get_device(db: Session, device_id: int) -> Device | None:
    return db.query(Device).filter(Device.id == device_id).first()


def get_device_by_serial(db: Session, serial_number: str) -> Device | None:
    return db.query(Device).filter(Device.serial_number == serial_number).first()


def create_device(db: Session, data: DeviceCreate) -> Device:
    nuevo = Device(**data.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def update_device(db: Session, device: Device, data: DeviceUpdate) -> Device:
    for campo, valor in data.model_dump().items():
        setattr(device, campo, valor)
    db.commit()
    db.refresh(device)
    return device


def patch_device(db: Session, device: Device, changes: dict) -> Device:
    for campo, valor in changes.items():
        setattr(device, campo, valor)
    db.commit()
    db.refresh(device)
    return device


def delete_device(db: Session, device: Device) -> None:
    db.delete(device)
    db.commit()
