"""Rutas del recurso `users` — protegidas con autenticación/roles.

La creación de usuarios se hace por POST /auth/register. Aquí quedan la consulta
(usuario autenticado) y la administración (solo admin).
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.dependencies.auth_dependency import get_current_active_user, require_admin
from app.dependencies.database_dependency import get_db
from app.dependencies.user_dependencies import get_user_or_404
from app.middlewares.rate_limit import limiter
from app.models.user_model import User
from app.schemas.loan_schema import LoanDetailResponse
from app.schemas.user_schema import UserPatch, UserResponse, UserRole, UserUpdate
from app.services import loan_service, user_service

router = APIRouter(prefix="/users", tags=["Users"])


# --- GET /users (autenticado, máx. 30/min) ----------------------------------
@router.get(
    "",
    response_model=list[UserResponse],
    summary="Listar usuarios",
    response_description="Lista de usuarios (filtrada y ordenada)",
    dependencies=[Depends(get_current_active_user)],
)
@limiter.limit("30/minute")
def listar_usuarios(
    request: Request,
    role: UserRole | None = Query(default=None, description="Filtra por rol"),
    is_active: bool | None = Query(default=None, description="Filtra por estado activo"),
    order_by: Literal["name", "created_at"] = Query(default="name", description="Ordenar por"),
    db: Session = Depends(get_db),
):
    """Lista usuarios (requiere token). Admite `?role=`, `?is_active=`, `?order_by=`."""
    return user_service.get_users(
        db, role=role.value if role else None, is_active=is_active, order_by=order_by
    )


# --- GET /users/{user_id} (autenticado) -------------------------------------
@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Consultar usuario por ID",
    response_description="Datos del usuario solicitado",
    dependencies=[Depends(get_current_active_user)],
)
def obtener_usuario(user: User = Depends(get_user_or_404)):
    """Consulta un usuario por su id (requiere token). 404 si no existe."""
    return user


# --- GET /users/{user_id}/loans (autenticado) -------------------------------
@router.get(
    "/{user_id}/loans",
    response_model=list[LoanDetailResponse],
    summary="Préstamos de un usuario",
    response_description="Dispositivos prestados al usuario (con joins)",
    dependencies=[Depends(get_current_active_user)],
)
def prestamos_del_usuario(user: User = Depends(get_user_or_404), db: Session = Depends(get_db)):
    """Lista los préstamos de un usuario con la info del dispositivo (join)."""
    prestamos = loan_service.get_user_loans(db, user.id)
    return [
        {
            "loan_id": p.id, "status": p.status, "loan_date": p.loan_date,
            "return_date": p.return_date, "user": p.user, "device": p.device,
        }
        for p in prestamos
    ]


# --- PUT /users/{user_id} (solo admin) --------------------------------------
@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario (completo)",
    dependencies=[Depends(require_admin)],
)
def reemplazar_usuario(
    datos: UserUpdate,
    user: User = Depends(get_user_or_404),
    db: Session = Depends(get_db),
):
    """Reemplaza los datos del usuario. Solo admin. 400 si el correo ya lo usa otro."""
    existente = user_service.get_user_by_email(db, datos.email)
    if existente and existente.id != user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"El correo {datos.email} ya está registrado por otro usuario")
    return user_service.update_user(db, user, datos)


# --- PATCH /users/{user_id} (solo admin) ------------------------------------
@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario (parcial)",
    dependencies=[Depends(require_admin)],
)
def actualizar_usuario_parcial(
    datos: UserPatch,
    user: User = Depends(get_user_or_404),
    db: Session = Depends(get_db),
):
    """Actualiza solo lo enviado. Solo admin. PATCH vacío -> 400."""
    cambios = datos.model_dump(mode="json", exclude_unset=True)
    if not cambios:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Debe enviar al menos un campo para actualizar")
    if "email" in cambios:
        existente = user_service.get_user_by_email(db, cambios["email"])
        if existente and existente.id != user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"El correo {cambios['email']} ya está registrado por otro usuario")
    return user_service.patch_user(db, user, cambios)


# --- DELETE /users/{user_id} (solo admin) -----------------------------------
@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar usuario",
    dependencies=[Depends(require_admin)],
)
def eliminar_usuario(user: User = Depends(get_user_or_404), db: Session = Depends(get_db)):
    """Elimina un usuario. Solo admin. 404 si no existe."""
    user_service.delete_user(db, user)
