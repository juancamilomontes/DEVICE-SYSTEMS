"""Rutas (endpoints) del recurso `users` — ahora sobre base de datos.

Las rutas reciben la sesión de BD con Depends(get_db), delegan la lógica en el
servicio y usan get_user_or_404 para el chequeo de existencia.
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies.database_dependency import get_db
from app.dependencies.user_dependencies import get_user_or_404, verify_api_key
from app.models.user_model import User
from app.schemas.loan_schema import LoanDetailResponse
from app.schemas.user_schema import UserCreate, UserPatch, UserResponse, UserRole, UserUpdate
from app.services import loan_service, user_service

router = APIRouter(prefix="/users", tags=["Users"])


# --- GET /users -------------------------------------------------------------
@router.get(
    "",
    response_model=list[UserResponse],
    summary="Listar usuarios",
    response_description="Lista de usuarios (filtrada y ordenada)",
)
def listar_usuarios(
    role: UserRole | None = Query(default=None, description="Filtra por rol"),
    is_active: bool | None = Query(default=None, description="Filtra por estado activo"),
    order_by: Literal["name", "created_at"] = Query(default="name", description="Ordenar por"),
    db: Session = Depends(get_db),
):
    """Lista usuarios. Admite `?role=`, `?is_active=` y `?order_by=`."""
    return user_service.get_users(
        db,
        role=role.value if role else None,
        is_active=is_active,
        order_by=order_by,
    )


# --- GET /users/{user_id} ---------------------------------------------------
@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Consultar usuario por ID",
    response_description="Datos del usuario solicitado",
)
def obtener_usuario(user: User = Depends(get_user_or_404)):
    """Consulta un usuario por su id. 404 si no existe."""
    return user


# --- GET /users/{user_id}/loans ---------------------------------------------
@router.get(
    "/{user_id}/loans",
    response_model=list[LoanDetailResponse],
    summary="Préstamos de un usuario",
    response_description="Dispositivos prestados al usuario (con joins)",
)
def prestamos_del_usuario(user: User = Depends(get_user_or_404), db: Session = Depends(get_db)):
    """Lista los préstamos de un usuario con la info del dispositivo (join)."""
    prestamos = loan_service.get_user_loans(db, user.id)
    return [
        {
            "loan_id": p.id,
            "status": p.status,
            "loan_date": p.loan_date,
            "return_date": p.return_date,
            "user": p.user,
            "device": p.device,
        }
        for p in prestamos
    ]


# --- POST /users ------------------------------------------------------------
@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
    response_description="Usuario creado",
)
def crear_usuario(datos: UserCreate, db: Session = Depends(get_db)):
    """Crea un usuario. Rechaza correos duplicados con 400."""
    if user_service.get_user_by_email(db, datos.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El correo {datos.email} ya está registrado",
        )
    return user_service.create_user(db, datos)


# --- PUT /users/{user_id} ---------------------------------------------------
@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario (completo)",
    response_description="Usuario reemplazado por completo",
)
def reemplazar_usuario(
    datos: UserUpdate,
    user: User = Depends(get_user_or_404),
    db: Session = Depends(get_db),
):
    """Reemplaza TODOS los campos. 404 si no existe, 400 si el correo ya lo usa otro."""
    existente = user_service.get_user_by_email(db, datos.email)
    if existente and existente.id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El correo {datos.email} ya está registrado por otro usuario",
        )
    return user_service.update_user(db, user, datos)


# --- PATCH /users/{user_id} -------------------------------------------------
@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario (parcial)",
    response_description="Usuario actualizado parcialmente",
)
def actualizar_usuario_parcial(
    datos: UserPatch,
    user: User = Depends(get_user_or_404),
    db: Session = Depends(get_db),
):
    """Actualiza solo lo enviado. PATCH vacío -> 400. 404 si no existe."""
    cambios = datos.model_dump(mode="json", exclude_unset=True)
    if not cambios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe enviar al menos un campo para actualizar",
        )
    if "email" in cambios:
        existente = user_service.get_user_by_email(db, cambios["email"])
        if existente and existente.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El correo {cambios['email']} ya está registrado por otro usuario",
            )
    return user_service.patch_user(db, user, cambios)


# --- DELETE /users/{user_id} ------------------------------------------------
@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar usuario",
    response_description="Usuario eliminado (sin contenido)",
    dependencies=[Depends(verify_api_key)],
)
def eliminar_usuario(
    user: User = Depends(get_user_or_404),
    db: Session = Depends(get_db),
):
    """Elimina un usuario. 204 sin cuerpo. Requiere cabecera X-API-Key. 404 si no existe."""
    user_service.delete_user(db, user)
