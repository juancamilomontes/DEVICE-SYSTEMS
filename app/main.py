"""Punto de entrada de la API device_systems (v5.0 — seguridad).

Añade autenticación OAuth2/JWT, CORS, middleware de trazabilidad y rate limiting
sobre el sistema de usuarios, dispositivos y préstamos.
"""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.auth.auth_routes import router as auth_router
from app.dependencies.user_dependencies import get_api_settings
from app.middlewares.rate_limit import limiter
from app.middlewares.request_middleware import RequestContextMiddleware
from app.routes import device_routes, loan_routes, user_routes

description = """
API REST **segura** de device_systems para gestionar usuarios, dispositivos y préstamos.

Versión 5.0: **autenticación OAuth2/JWT**, contraseñas con **hash (passlib)**,
**rutas protegidas por rol**, **CORS**, **middleware** de trazabilidad y **rate limiting**.
"""

tags_metadata = [
    {"name": "Auth", "description": "Registro, login (OAuth2/JWT) y perfil del usuario."},
    {"name": "Users", "description": "Gestión de usuarios (rutas protegidas)."},
    {"name": "Devices", "description": "Gestión de dispositivos."},
    {"name": "Loans", "description": "Préstamos y consultas con joins."},
    {"name": "Security", "description": "Información sobre las protecciones de la API."},
    {"name": "root", "description": "Bienvenida, estado e información."},
]

app = FastAPI(
    title="device_systems API",
    description=description,
    version="5.0.0",
    contact={"name": "Juan Camilo Montes", "email": "jm3876602@gmail.com"},
    openapi_tags=tags_metadata,
)

# --- Rate limiting (slowapi) ------------------------------------------------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# --- CORS -------------------------------------------------------------------
# Solo se permiten estos orígenes (frontend local). Con allow_credentials=True
# NO se puede usar "*": el navegador rechaza credenciales con origen comodín
# (ver explicación en el README).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Middleware personalizado de trazabilidad -------------------------------
app.add_middleware(RequestContextMiddleware)

# --- Routers ----------------------------------------------------------------
app.include_router(auth_router)
app.include_router(user_routes.router)
app.include_router(device_routes.router)
app.include_router(loan_routes.router)


# --- Endpoints de bienvenida / estado / info / seguridad --------------------
@app.get("/", tags=["root"], summary="Mensaje de bienvenida")
def read_root():
    return {"message": "Bienvenido a la API de device_systems!"}


@app.get("/estado", tags=["root"], summary="Estado de la aplicación")
def read_estado():
    return {"Estado": "La aplicación está funcionando correctamente.", "server": "FastAPI"}


@app.get("/info", tags=["root"], summary="Información/configuración de la API")
def read_info(settings: dict = Depends(get_api_settings)):
    return settings


@app.get("/security/status", tags=["Security"], summary="Protecciones activas")
def security_status():
    """Resumen de los mecanismos de seguridad activos en la API."""
    return {
        "auth": "OAuth2 + JWT",
        "password_hashing": "passlib (bcrypt)",
        "cors": ["http://localhost:5173", "http://localhost:3000"],
        "rate_limiting": True,
        "middleware": ["X-App-Name", "X-Process-Time", "X-Request-ID"],
    }
