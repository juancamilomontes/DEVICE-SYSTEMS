"""Configuración del rate limiting con slowapi.

`limiter` se importa tanto en main.py (para registrarlo y su manejador de error)
como en las rutas (para aplicar los límites con el decorador @limiter.limit).
La clave de conteo es la IP del cliente (get_remote_address).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
