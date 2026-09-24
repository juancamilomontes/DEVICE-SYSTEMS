"""Seguridad: hash de contraseñas (passlib) y tokens JWT (python-jose).

Regla de oro: NINGUNA contraseña se guarda ni se muestra en texto plano.
Solo se guarda su hash; para entrar se compara el texto con el hash.
"""

import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext

# Carga variables desde .env (SECRET_KEY, etc.).
load_dotenv()

# Configuración leída del entorno (con valores por defecto para desarrollo).
SECRET_KEY = os.getenv("SECRET_KEY", "clave-secreta-solo-para-desarrollo-cambiar")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Contexto de passlib con el algoritmo bcrypt.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- Contraseñas ------------------------------------------------------------
def get_password_hash(password: str) -> str:
    """Devuelve el hash seguro de una contraseña (para guardar en la BD)."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compara la contraseña en texto plano con el hash guardado."""
    return pwd_context.verify(plain_password, hashed_password)


# --- Tokens JWT -------------------------------------------------------------
def create_access_token(data: dict) -> str:
    """Crea un token JWT firmado con la fecha de expiración incluida."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Valida y decodifica un token JWT. Devuelve el payload o None si es inválido."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# --- Validación de fuerza de contraseña (reutilizable por los schemas) ------
def validate_password_strength(password: str) -> str:
    """Valida una contraseña segura y la devuelve, o lanza ValueError.

    Reglas: mínimo 8 caracteres, al menos una mayúscula, una minúscula,
    un número y sin espacios en blanco.
    """
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    if not any(c.isupper() for c in password):
        raise ValueError("La contraseña debe tener al menos una mayúscula")
    if not any(c.islower() for c in password):
        raise ValueError("La contraseña debe tener al menos una minúscula")
    if not any(c.isdigit() for c in password):
        raise ValueError("La contraseña debe tener al menos un número")
    if any(c.isspace() for c in password):
        raise ValueError("La contraseña no debe tener espacios en blanco")
    return password
