"""Rutas (endpoints) del recurso `users`.

Las rutas son "delgadas": validan/reciben datos, delegan la lógica en la capa
de servicios y usan dependencias (`Depends`) para lo reutilizable. No conocen
cómo se guardan los usuarios.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies.user_dependencies import (
    get_user_or_404,
    get_user_service,
    verify_api_key,
)
from app.schemas.user_schema import UserCreate, UserResponse, UserRole, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


# --- GET /users -------------------------------------------------------------
@router.get(
    "",
    response_model=list[UserResponse],
    summary="Listar usuarios",
    response_description="Lista de usuarios (opcionalmente filtrada)",
)
def listar_usuarios(
    role: UserRole | None = Query(default=None, description="Filtra por rol"),
    is_active: bool | None = Query(default=None, description="Filtra por estado activo"),
    service: UserService = Depends(get_user_service),
):
    """Lista todos los usuarios. Admite filtros `?role=` y `?is_active=`."""
    return service.list_users(role.value if role else None, is_active)


# --- GET /users/{user_id} ---------------------------------------------------
@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Consultar usuario por ID",
    response_description="Datos del usuario solicitado",
)
def obtener_usuario(user: dict = Depends(get_user_or_404)):
    """Consulta un usuario por su id. Devuelve 404 si no existe."""
    return user


# --- POST /users ------------------------------------------------------------
@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario",
    response_description="Usuario creado",
)
def crear_usuario(
    datos: UserCreate,
    service: UserService = Depends(get_user_service),
):
    """Registra un nuevo usuario. Rechaza correos duplicados con 400."""
    if service.email_exists(datos.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El correo {datos.email} ya está registrado",
        )
    return service.create_user(datos)


# --- PUT /users/{user_id} ---------------------------------------------------
@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario (completo)",
    response_description="Usuario reemplazado por completo",
)
def reemplazar_usuario(
    datos: UserCreate,
    user: dict = Depends(get_user_or_404),
    service: UserService = Depends(get_user_service),
):
    """Reemplaza TODOS los campos de un usuario existente.

    Requiere enviar name, email, role e is_active. Devuelve 404 si no existe
    y 400 si el nuevo correo ya lo usa otro usuario.
    """
    if service.email_exists(datos.email, exclude_id=user["id"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El correo {datos.email} ya está registrado por otro usuario",
        )
    return service.replace_user(user, datos)


# --- PATCH /users/{user_id} -------------------------------------------------
@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Actualizar usuario (parcial)",
    response_description="Usuario actualizado parcialmente",
)
def actualizar_usuario_parcial(
    datos: UserUpdate,
    user: dict = Depends(get_user_or_404),
    service: UserService = Depends(get_user_service),
):
    """Actualiza solo los campos enviados.

    Si no se envía ningún campo, responde 400. 404 si el usuario no existe y
    400 si el nuevo correo ya lo usa otro usuario.
    """
    # exclude_unset=True => solo lo que el cliente envió realmente.
    cambios = datos.model_dump(mode="json", exclude_unset=True)
    if not cambios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe enviar al menos un campo para actualizar",
        )
    if "email" in cambios and service.email_exists(cambios["email"], exclude_id=user["id"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El correo {cambios['email']} ya está registrado por otro usuario",
        )
    return service.apply_changes(user, cambios)


# --- DELETE /users/{user_id} ------------------------------------------------
@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar usuario",
    response_description="Usuario eliminado (sin contenido)",
    dependencies=[Depends(verify_api_key)],
)
def eliminar_usuario(
    user: dict = Depends(get_user_or_404),
    service: UserService = Depends(get_user_service),
):
    """Elimina un usuario existente. Devuelve 204 sin cuerpo.

    Requiere la cabecera `X-API-Key: device-systems-2026` (auth simulada).
    404 si el usuario no existe.
    """
    service.delete_user(user)
