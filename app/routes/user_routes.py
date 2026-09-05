"""Rutas (endpoints) del recurso `users`.

Como esta actividad es de fundamentos de FastAPI, NO se usa base de datos:
los usuarios se guardan en una lista en memoria (se reinicia al reiniciar el
servidor). Eso es suficiente para practicar GET, POST, path/query params,
validación con Pydantic y response models.
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.user_schema import UserCreate, UserResponse, UserRole

# prefix="/users" => todas las rutas de aquí empiezan por /users
# tags=["users"] => las agrupa en la documentación de Swagger
router = APIRouter(prefix="/users", tags=["users"])


# --- "Base de datos" en memoria ---------------------------------------------
# Cada usuario es un dict. Se siembran algunos para que los GET devuelvan datos.
_users: list[dict] = [
    {"id": 1, "name": "Juan Camilo Montes", "email": "juanca@device.com", "role": "admin", "is_active": True},
    {"id": 2, "name": "Ana Soporte", "email": "ana@device.com", "role": "support", "is_active": True},
    {"id": 3, "name": "Pedro Perez", "email": "pedro@device.com", "role": "user", "is_active": False},
]

# Contador para asignar el próximo id. Empieza después del último sembrado.
_next_id = 4


# --- GET /users -------------------------------------------------------------
@router.get("", response_model=list[UserResponse])
def listar_usuarios(
    # Query params OPCIONALES: si no se envían, quedan en None y no se filtra.
    role: UserRole | None = Query(default=None, description="Filtra por rol: admin, support o user"),
    is_active: bool | None = Query(default=None, description="Filtra por estado activo (true/false)"),
):
    """Lista todos los usuarios.

    Soporta filtros por query param:
    - `GET /users`                -> todos
    - `GET /users?role=admin`     -> solo los admin
    - `GET /users?is_active=true` -> solo los activos
    (se pueden combinar: `GET /users?role=user&is_active=false`)
    """
    resultado = _users

    if role is not None:
        # role.value es el texto ("admin"), que es como se guarda en el dict.
        resultado = [u for u in resultado if u["role"] == role.value]

    if is_active is not None:
        resultado = [u for u in resultado if u["is_active"] == is_active]

    return resultado


# --- GET /users/{user_id} ---------------------------------------------------
@router.get("/{user_id}", response_model=UserResponse)
def obtener_usuario(user_id: int):
    """Consulta un usuario por su id (Path Parameter).

    Si no existe, devuelve 404.
    """
    for u in _users:
        if u["id"] == user_id:
            return u

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No existe un usuario con id {user_id}",
    )


# --- POST /users ------------------------------------------------------------
@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(datos: UserCreate):
    """Registra un nuevo usuario.

    - Valida la entrada con Pydantic (nombre, correo, rol, estado).
    - Rechaza correos duplicados con 409.
    - Devuelve el usuario creado (con su id) usando el response_model.
    """
    global _next_id

    # Evitar correos duplicados (comparando sin distinguir mayúsculas).
    correo = datos.email.lower()
    for u in _users:
        if u["email"].lower() == correo:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El correo {datos.email} ya está registrado",
            )

    nuevo = {
        "id": _next_id,
        "name": datos.name,
        "email": datos.email,
        "role": datos.role.value,
        "is_active": datos.is_active,
    }
    _users.append(nuevo)
    _next_id += 1

    return nuevo
