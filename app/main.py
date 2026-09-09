"""Punto de entrada de la API device_systems (versión 3.0 — con persistencia).

Crea la aplicación FastAPI, crea las tablas en la base de datos al arrancar,
sirve la documentación (Swagger/ReDoc) y agrega cabeceras HTTP personalizadas.
"""

from fastapi import Depends, FastAPI, Request

from app.database.connection import Base, SessionLocal, engine
from app.dependencies.user_dependencies import get_api_settings
from app.models.user_model import User  # importa el modelo para que create_all lo conozca
from app.routes import user_routes

# Crea las tablas en la base de datos si no existen (usa los modelos que heredan
# de Base). Con SQLite, esto genera el archivo device_systems.db al arrancar.
Base.metadata.create_all(bind=engine)


def _sembrar_datos_iniciales() -> None:
    """Inserta 3 usuarios de ejemplo SOLO si la tabla está vacía.

    Sirve para que los GET muestren datos la primera vez. Como es persistente,
    en los siguientes arranques ya hay datos y no se vuelve a sembrar.
    """
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            db.add_all([
                User(name="Juan Camilo Montes", email="juanca@device.com", role="admin", is_active=True),
                User(name="Ana Soporte", email="ana@device.com", role="support", is_active=True),
                User(name="Pedro Perez", email="pedro@device.com", role="user", is_active=False),
            ])
            db.commit()
    finally:
        db.close()


_sembrar_datos_iniciales()


description = """
API REST para la gestión de **usuarios** del sistema **device_systems**.

Versión 3.0: los usuarios se **persisten en una base de datos** (SQLite) mediante
**SQLAlchemy**. Incluye el CRUD completo del recurso `/users` con validaciones,
constraints, manejo de errores, documentación Swagger/OpenAPI e inyección de
dependencias (`Depends()`).
"""

tags_metadata = [
    {"name": "Users", "description": "Operaciones CRUD sobre el recurso usuarios (en base de datos)."},
    {"name": "root", "description": "Endpoints de bienvenida, estado e información de la API."},
]

app = FastAPI(
    title="device_systems API",
    description=description,
    version="3.0.0",
    contact={"name": "Juan Camilo Montes", "email": "jm3876602@gmail.com"},
    openapi_tags=tags_metadata,
)


# --- Middleware: cabeceras HTTP personalizadas ------------------------------
@app.middleware("http")
async def agregar_cabeceras_personalizadas(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-App-Name"] = "device_systems"
    response.headers["X-API-Version"] = "3.0"
    return response


app.include_router(user_routes.router)


# --- Endpoints de bienvenida / salud / info ---------------------------------
@app.get("/", tags=["root"], summary="Mensaje de bienvenida")
def read_root():
    return {"message": "Bienvenido a la API de device_systems!"}


@app.get("/estado", tags=["root"], summary="Estado de la aplicación")
def read_estado():
    return {
        "Estado": "La aplicación está funcionando correctamente.",
        "server": "FastAPI",
    }


@app.get("/info", tags=["root"], summary="Información/configuración de la API")
def read_info(settings: dict = Depends(get_api_settings)):
    """Devuelve la configuración general de la API (inyectada con Depends)."""
    return settings
