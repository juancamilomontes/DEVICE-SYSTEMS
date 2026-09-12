"""Punto de entrada de la API device_systems (v4.0 — relaciones y migraciones).

Ahora el esquema de la base de datos lo gestiona **Alembic** (migraciones), por
eso este archivo ya NO crea tablas: primero corres `alembic upgrade head` y
luego arrancas el servidor.
"""

from fastapi import Depends, FastAPI, Request

from app.dependencies.user_dependencies import get_api_settings
from app.routes import device_routes, loan_routes, user_routes

description = """
API REST del sistema **device_systems** para gestionar **usuarios**, **dispositivos**
y **préstamos**.

Versión 4.0: incorpora **migraciones con Alembic**, **relaciones entre modelos**
(User ↔ Loan ↔ Device) y **consultas con joins y filtros avanzados**.
"""

tags_metadata = [
    {"name": "Users", "description": "Gestión de usuarios y sus préstamos."},
    {"name": "Devices", "description": "Gestión de dispositivos e historial de préstamos."},
    {"name": "Loans", "description": "Préstamos: crear, devolver y consultar con datos relacionados."},
    {"name": "root", "description": "Bienvenida, estado e información de la API."},
]

app = FastAPI(
    title="device_systems API",
    description=description,
    version="4.0.0",
    contact={"name": "Juan Camilo Montes", "email": "jm3876602@gmail.com"},
    openapi_tags=tags_metadata,
)


# --- Middleware: cabeceras HTTP personalizadas ------------------------------
@app.middleware("http")
async def agregar_cabeceras_personalizadas(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-App-Name"] = "device_systems"
    response.headers["X-API-Version"] = "4.0"
    return response


# Registra los tres recursos.
app.include_router(user_routes.router)
app.include_router(device_routes.router)
app.include_router(loan_routes.router)


# --- Endpoints de bienvenida / salud / info ---------------------------------
@app.get("/", tags=["root"], summary="Mensaje de bienvenida")
def read_root():
    return {"message": "Bienvenido a la API de device_systems!"}


@app.get("/estado", tags=["root"], summary="Estado de la aplicación")
def read_estado():
    return {"Estado": "La aplicación está funcionando correctamente.", "server": "FastAPI"}


@app.get("/info", tags=["root"], summary="Información/configuración de la API")
def read_info(settings: dict = Depends(get_api_settings)):
    """Devuelve la configuración general de la API (inyectada con Depends)."""
    return settings
