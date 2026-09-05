"""Rutas (endpoints) del recurso `users`.

Las rutas son "delgadas": validan/reciben datos, delegan la lógica en la capa
de servicios y usan dependencias (`Depends`) para lo reutilizable. No conocen
cómo se guardan los usuarios.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies.user_dependencies import get_user_or_404, get_user_service
from app.schemas.user_schema import UserCreate, UserResponse, UserRole
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
