"""Rutas de autenticación: registro, login (OAuth2/JWT) y perfil."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import auth_service
from app.auth.security import create_access_token
from app.dependencies.auth_dependency import get_current_active_user
from app.dependencies.database_dependency import get_db
from app.middlewares.rate_limit import limiter
from app.models.user_model import User
from app.schemas.auth_schema import Token, UserRegister
from app.schemas.user_schema import UserResponse
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED,
             summary="Registrar usuario",
             response_description="Usuario creado (sin exponer la contraseña)")
@limiter.limit("3/minute")
def register(request: Request, datos: UserRegister, db: Session = Depends(get_db)):
    """Registra un usuario con contraseña segura. Rechaza correos duplicados (400).

    La contraseña se guarda **hasheada**; nunca en texto plano.
    """
    if user_service.get_user_by_email(db, datos.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"El correo {datos.email} ya está registrado")
    return auth_service.register_user(db, datos)


@router.post("/login", response_model=Token, summary="Iniciar sesión (obtener token)",
             response_description="Token JWT de acceso")
@limiter.limit("5/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(get_db)):
    """Autentica al usuario (usuario = email) y devuelve un token JWT.

    401 si las credenciales son incorrectas.
    """
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # El "sub" del token es el correo del usuario.
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse, summary="Perfil del usuario autenticado",
            response_description="Datos del usuario del token (sin contraseña)")
def me(current_user: User = Depends(get_current_active_user)):
    """Devuelve los datos del usuario autenticado. Requiere token válido (401 si no)."""
    return current_user
