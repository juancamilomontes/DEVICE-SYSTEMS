"""Rutas del recurso `loans` (préstamos): creación, devolución y consultas con joins."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies.database_dependency import get_db
from app.models.loan_model import Loan
from app.schemas.loan_schema import LoanCreate, LoanDetailResponse, LoanResponse
from app.services import device_service, loan_service, user_service

router = APIRouter(prefix="/loans", tags=["Loans"])


def _a_detalle(loan: Loan) -> dict:
    """Arma la respuesta con la info relacionada de usuario y dispositivo."""
    return {
        "loan_id": loan.id,
        "status": loan.status,
        "loan_date": loan.loan_date,
        "return_date": loan.return_date,
        "user": loan.user,
        "device": loan.device,
    }


# --- GET /loans -------------------------------------------------------------
@router.get("", response_model=list[LoanResponse], summary="Listar préstamos",
            response_description="Lista de préstamos (filtrada)")
def listar_prestamos(
    status_: str | None = Query(default=None, alias="status", description="Filtra por estado"),
    user_email: str | None = Query(default=None, description="Filtra por correo del usuario (join)"),
    device_type: str | None = Query(default=None, description="Filtra por tipo de dispositivo (join)"),
    db: Session = Depends(get_db),
):
    """Lista préstamos. Soporta `?status=`, `?user_email=`, `?device_type=`."""
    return loan_service.get_loans(db, status=status_, user_email=user_email, device_type=device_type)


# --- GET /loans/details (¡antes de /{loan_id}!) -----------------------------
@router.get("/details", response_model=list[LoanDetailResponse],
            summary="Listar préstamos con detalle de usuario y dispositivo")
def listar_prestamos_detalle(
    status_: str | None = Query(default=None, alias="status"),
    user_email: str | None = Query(default=None),
    device_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Préstamos con la información relacionada (usuario + dispositivo) vía joins."""
    prestamos = loan_service.get_loans(db, status=status_, user_email=user_email, device_type=device_type)
    return [_a_detalle(p) for p in prestamos]


# --- GET /loans/{loan_id} ---------------------------------------------------
@router.get("/{loan_id}", response_model=LoanDetailResponse, summary="Consultar préstamo por ID")
def obtener_prestamo(loan_id: int, db: Session = Depends(get_db)):
    """Consulta un préstamo por id, con datos de usuario y dispositivo. 404 si no existe."""
    loan = loan_service.get_loan(db, loan_id)
    if loan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Préstamo no encontrado")
    return _a_detalle(loan)


# --- POST /loans ------------------------------------------------------------
@router.post("", response_model=LoanDetailResponse, status_code=status.HTTP_201_CREATED,
             summary="Registrar préstamo",
             response_description="Préstamo creado con usuario y dispositivo")
def crear_prestamo(datos: LoanCreate, db: Session = Depends(get_db)):
    """Presta un dispositivo a un usuario.

    Valida que el usuario exista (404), que el dispositivo exista (404) y que
    esté disponible (409). Al crear, marca el dispositivo como no disponible.
    """
    usuario = user_service.get_user(db, datos.user_id)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    device = device_service.get_device(db, datos.device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispositivo no encontrado")

    if not device.is_available:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="El dispositivo no está disponible para préstamo")

    loan = loan_service.create_loan(db, datos.user_id, device)
    return _a_detalle(loan)


# --- PATCH /loans/{loan_id}/return ------------------------------------------
@router.patch("/{loan_id}/return", response_model=LoanDetailResponse,
              summary="Devolver dispositivo",
              response_description="Préstamo marcado como devuelto")
def devolver_prestamo(loan_id: int, db: Session = Depends(get_db)):
    """Marca un préstamo como devuelto y libera el dispositivo.

    404 si el préstamo no existe; 409 si ya estaba devuelto.
    """
    loan = loan_service.get_loan(db, loan_id)
    if loan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Préstamo no encontrado")
    if loan.status == "returned":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="El préstamo ya fue devuelto")

    loan = loan_service.return_loan(db, loan)
    return _a_detalle(loan)
