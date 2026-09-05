"""Punto de entrada de la API device_systems.

Crea la aplicación FastAPI, registra el router de usuarios y agrega un
middleware que devuelve cabeceras HTTP personalizadas en cada respuesta.
"""

from fastapi import FastAPI, Request

from app.routes import user_routes

# title/version/description alimentan la documentación automática de Swagger UI.
app = FastAPI(
    title="device_systems",
    version="1.0",
    description="API REST para la gestión de usuarios del sistema device_systems.",
)


# --- Middleware: cabeceras HTTP personalizadas (Fase 5) ---------------------
# Se ejecuta en cada petición y agrega las cabeceras a TODAS las respuestas.
@app.middleware("http")
async def agregar_cabeceras_personalizadas(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-App-Name"] = "device_systems"
    response.headers["X-API-Version"] = "1.0"
    return response


# Registra todas las rutas de /users definidas en user_routes.py
app.include_router(user_routes.router)


# --- Endpoints de bienvenida / salud ----------------------------------------
@app.get("/", tags=["root"])
def read_root():
    return {"message": "Bienvenido a la API de device_systems!"}


@app.get("/estado", tags=["root"])
def read_estado():
    return {
        "Estado": "La aplicación está funcionando correctamente.",
        "server": "FastAPI",
    }
