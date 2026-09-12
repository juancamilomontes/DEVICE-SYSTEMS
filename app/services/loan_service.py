"""Lógica de negocio del recurso `loans`.

Incluye las reglas de negocio (prestar / devolver) y las consultas con JOINS
que combinan préstamos + usuarios + dispositivos.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from app.models.device_model import Device
from app.models.loan_model import Loan
from app.models.user_model import User


def get_loans(
    db: Session,
    status: str | None = None,
    user_email: str | None = None,
    device_type: str | None = None,
    user_id: int | None = None,
    device_id: int | None = None,
) -> list[Loan]:
    """Lista préstamos con filtros opcionales.

    Usa JOINS a users/devices cuando se filtra por correo del usuario o por tipo
    de dispositivo. `joinedload` trae de una vez los datos relacionados.
    """
    query = db.query(Loan).options(joinedload(Loan.user), joinedload(Loan.device))

    if status is not None:
        query = query.filter(Loan.status == status)
    if user_id is not None:
        query = query.filter(Loan.user_id == user_id)
    if device_id is not None:
        query = query.filter(Loan.device_id == device_id)
    if user_email is not None:
        # join con users + filtro por correo (ilike = sin distinguir mayúsculas).
        query = query.join(User).filter(User.email.ilike(f"%{user_email}%"))
    if device_type is not None:
        # join con devices + filtro por tipo.
        query = query.join(Device).filter(Device.device_type == device_type)

    return query.order_by(Loan.loan_date.desc()).all()


def get_loan(db: Session, loan_id: int) -> Loan | None:
    return (
        db.query(Loan)
        .options(joinedload(Loan.user), joinedload(Loan.device))
        .filter(Loan.id == loan_id)
        .first()
    )


def get_user_loans(db: Session, user_id: int) -> list[Loan]:
    """Préstamos de un usuario (con datos del dispositivo)."""
    return get_loans(db, user_id=user_id)


def get_device_loans(db: Session, device_id: int) -> list[Loan]:
    """Historial de préstamos de un dispositivo."""
    return get_loans(db, device_id=device_id)


def create_loan(db: Session, user_id: int, device: Device) -> Loan:
    """Crea el préstamo y marca el dispositivo como NO disponible."""
    prestamo = Loan(user_id=user_id, device_id=device.id, status="active")
    device.is_available = False  # ya no se puede prestar de nuevo
    db.add(prestamo)
    db.commit()
    db.refresh(prestamo)
    return prestamo


def return_loan(db: Session, loan: Loan) -> Loan:
    """Marca el préstamo como devuelto y libera el dispositivo."""
    loan.status = "returned"
    loan.return_date = datetime.now(timezone.utc)
    loan.device.is_available = True  # vuelve a estar disponible
    db.commit()
    db.refresh(loan)
    return loan
