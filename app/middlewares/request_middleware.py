"""Middleware personalizado de trazabilidad.

En cada petición:
- mide el tiempo de respuesta,
- agrega las cabeceras X-App-Name, X-Process-Time, X-API-Version y X-Request-ID,
- propaga el X-Request-ID entrante o genera uno nuevo,
- registra en el log el método, la ruta y el código de estado.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("device_systems")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        inicio = time.perf_counter()

        # Usa el X-Request-ID que venga, o genera uno nuevo (correlation ID).
        request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:8])

        response = await call_next(request)

        proceso = time.perf_counter() - inicio
        response.headers["X-App-Name"] = "device_systems"
        response.headers["X-API-Version"] = "5.0"
        response.headers["X-Process-Time"] = f"{proceso:.4f}"
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "%s %s -> %s (%.4fs) [rid=%s]",
            request.method, request.url.path, response.status_code, proceso, request_id,
        )
        return response
