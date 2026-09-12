"""Rutas del recurso `devices` (CRUD + filtros + historial de préstamos)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies.database_dependency import get_db
from app.dependencies.user_dependencies import verify_api_key
from app.models.device_model import Device
from app.schemas.device_schema import DeviceCreate, DevicePatch, DeviceResponse, DeviceUpdate
from app.schemas.loan_schema import LoanDetailResponse
from app.services import device_service, loan_service

router = APIRouter(prefix="/devices", tags=["Devices"])


def get_device_or_404(device_id: int, db: Session = Depends(get_db)) -> Device:
    """Dependencia: trae el dispositivo o lanza 404."""
    device = device_service.get_device(db, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispositivo no encontrado")
    return device


@router.get("", response_model=list[DeviceResponse], summary="Listar dispositivos",
            response_description="Lista de dispositivos (filtrada)")
def listar_dispositivos(
    device_type: str | None = Query(default=None, description="Filtra por tipo (laptop, tablet...)"),
    is_available: bool | None = Query(default=None, description="Filtra por disponibilidad"),
    brand: str | None = Query(default=None, description="Filtra por marca (contiene)"),
    search: str | None = Query(default=None, description="Busca en nombre o número de serie"),
    db: Session = Depends(get_db),
):
    """Lista dispositivos. Soporta `?device_type=`, `?is_available=`, `?brand=`, `?search=`."""
    return device_service.get_devices(db, device_type, is_available, brand, search)


@router.get("/{device_id}", response_model=DeviceResponse, summary="Consultar dispositivo por ID")
def obtener_dispositivo(device: Device = Depends(get_device_or_404)):
    """Consulta un dispositivo por id. 404 si no existe."""
    return device


@router.get("/{device_id}/loans", response_model=list[LoanDetailResponse],
            summary="Historial de préstamos del dispositivo")
def prestamos_del_dispositivo(device: Device = Depends(get_device_or_404), db: Session = Depends(get_db)):
    """Devuelve el historial de préstamos de un dispositivo (con joins)."""
    prestamos = loan_service.get_device_loans(db, device.id)
    return [_a_detalle(p) for p in prestamos]


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED,
             summary="Crear dispositivo", response_description="Dispositivo creado")
def crear_dispositivo(datos: DeviceCreate, db: Session = Depends(get_db)):
    """Crea un dispositivo. Rechaza número de serie duplicado con 400."""
    if device_service.get_device_by_serial(db, datos.serial_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El número de serie {datos.serial_number} ya está registrado",
        )
    return device_service.create_device(db, datos)


@router.put("/{device_id}", response_model=DeviceResponse, summary="Actualizar dispositivo (completo)")
def reemplazar_dispositivo(datos: DeviceUpdate, device: Device = Depends(get_device_or_404),
                           db: Session = Depends(get_db)):
    """Reemplaza todos los campos. 404 si no existe, 400 si el serial ya lo usa otro."""
    existente = device_service.get_device_by_serial(db, datos.serial_number)
    if existente and existente.id != device.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"El número de serie {datos.serial_number} ya está registrado")
    return device_service.update_device(db, device, datos)


@router.patch("/{device_id}", response_model=DeviceResponse, summary="Actualizar dispositivo (parcial)")
def actualizar_dispositivo_parcial(datos: DevicePatch, device: Device = Depends(get_device_or_404),
                                   db: Session = Depends(get_db)):
    """Actualiza solo lo enviado. PATCH vacío -> 400."""
    cambios = datos.model_dump(exclude_unset=True)
    if not cambios:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Debe enviar al menos un campo para actualizar")
    if "serial_number" in cambios:
        existente = device_service.get_device_by_serial(db, cambios["serial_number"])
        if existente and existente.id != device.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"El número de serie {cambios['serial_number']} ya está registrado")
    return device_service.patch_device(db, device, cambios)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar dispositivo",
               dependencies=[Depends(verify_api_key)])
def eliminar_dispositivo(device: Device = Depends(get_device_or_404), db: Session = Depends(get_db)):
    """Elimina un dispositivo. Requiere cabecera X-API-Key. 404 si no existe."""
    device_service.delete_device(db, device)


def _a_detalle(loan) -> dict:
    """Arma el dict con la info relacionada (usuario + dispositivo)."""
    return {
        "loan_id": loan.id,
        "status": loan.status,
        "loan_date": loan.loan_date,
        "return_date": loan.return_date,
        "user": loan.user,
        "device": loan.device,
    }
