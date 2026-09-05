"""Punto de entrada de la API device_systems (versión 2.0).

Crea la aplicación FastAPI con metadatos completos para la documentación
automática (Swagger/OpenAPI y ReDoc), registra el router de usuarios y agrega
un middleware con cabeceras HTTP personalizadas.
"""

from fastapi import FastAPI, Request

from app.routes import user_routes

# Descripción larga (se muestra en la portada de Swagger UI / ReDoc).
description = """
API REST para la gestión de **usuarios** del sistema **device_systems**.

Incluye el **CRUD completo** del recurso `/users`:

* Crear, listar, consultar por id y filtrar (rol / estado).
* Actualización completa (**PUT**) y parcial (**PATCH**).
* Eliminación (**DELETE**) protegida con cabecera de API Key.
* Manejo de errores con códigos HTTP apropiados.
* Lógica reutilizable mediante **Dependency Injection** (`Depends()`).
"""

# Metadatos de los tags: agrupan y describen los endpoints en la documentación.
tags_metadata = [
    {"name": "Users", "description": "Operaciones CRUD sobre el recurso usuarios."},
    {"name": "root", "description": "Endpoints de bienvenida y estado de la API."},
]

app = FastAPI(
    title="device_systems API",
    description=description,
    version="2.0.0",
    contact={"name": "Juan Camilo Montes", "email": "jm3876602@gmail.com"},
    openapi_tags=tags_metadata,
)


# --- Middleware: cabeceras HTTP personalizadas ------------------------------
@app.middleware("http")
async def agregar_cabeceras_personalizadas(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-App-Name"] = "device_systems"
    response.headers["X-API-Version"] = "1.0"
    return response


# Registra todas las rutas de /users.
app.include_router(user_routes.router)


# --- Endpoints de bienvenida / salud ----------------------------------------
@app.get("/", tags=["root"], summary="Mensaje de bienvenida")
def read_root():
    return {"message": "Bienvenido a la API de device_systems!"}


@app.get("/estado", tags=["root"], summary="Estado de la aplicación")
def read_estado():
    return {
        "Estado": "La aplicación está funcionando correctamente.",
        "server": "FastAPI",
    }
