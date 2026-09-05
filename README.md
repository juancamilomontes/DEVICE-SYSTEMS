# device_systems — API REST de Usuarios (v2.0)

**Actividad:** GA1-220501096-01-AA1-EV08 — FastAPI Intermedio (CRUD completo, manejo de errores, Swagger/OpenAPI y Dependency Injection)
**Autor:** Juan Camilo Montes
**Programa:** Análisis y Desarrollo de Software (ADSO) — SENA

## Descripción

`device_systems` es una API REST construida con **FastAPI** para administrar el
recurso **usuarios**. En esta versión evoluciona de una API básica (GET/POST) a
una API profesional con **CRUD completo**, manejo de errores con `HTTPException`,
códigos de estado HTTP correctos, documentación automática (Swagger/OpenAPI y
ReDoc) y reutilización de lógica mediante **Dependency Injection** (`Depends()`).

> Los usuarios se guardan en una lista **en memoria** (`app/data/users_db.py`);
> los datos se reinician cada vez que se reinicia el servidor.

## Tecnologías utilizadas

- **Python 3.11+**
- **FastAPI** — framework de la API REST.
- **Uvicorn** — servidor ASGI.
- **Pydantic v2** — validación de datos y modelos de entrada/salida.
- **email-validator** — validación del formato de correo (`EmailStr`).
- **pytest** + **httpx** — pruebas automáticas.
- Gestor de dependencias: **uv**.

## Estructura del proyecto

El código está separado por responsabilidades (arquitectura en capas):

```
device_systems/
└── app/
    ├── main.py                      # crea la app, metadatos Swagger y middleware
    ├── routes/user_routes.py        # endpoints (capa de presentación)
    ├── schemas/user_schema.py       # modelos Pydantic de entrada/salida
    ├── services/user_service.py     # lógica de negocio (UserService)
    ├── dependencies/user_dependencies.py  # funciones reutilizables con Depends()
    └── data/users_db.py             # "base de datos" en memoria
```

- **routes**: define los endpoints; son "delgados" y delegan en los servicios.
- **schemas**: modelos Pydantic (`UserCreate`, `UserUpdate`, `UserResponse`).
- **services**: toda la lógica (buscar, crear, reemplazar, actualizar, eliminar).
- **dependencies**: lógica reutilizable inyectada con `Depends()`.
- **data**: simulación de base de datos en memoria.

## Modelo de Usuario

| Campo       | Tipo    | Validación                                       |
|-------------|---------|--------------------------------------------------|
| `id`        | int     | Lo asigna el servidor                            |
| `name`      | str     | Obligatorio, mínimo 3 caracteres                 |
| `email`     | EmailStr| Formato de correo válido y único                 |
| `role`      | enum    | Solo: `admin`, `support`, `user` (default `user`)|
| `is_active` | bool    | Default `true`                                   |

## Instalación de dependencias

Con **uv** (recomendado):

```bash
uv sync
```

O con **pip**:

```bash
pip install -r requirements.txt
```

## Ejecución del servidor

```bash
uv run uvicorn app.main:app --reload
```

Disponible en:

- API: http://127.0.0.1:8000
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## Tabla de endpoints

| Método | Ruta                    | Descripción                        | Códigos                |
|--------|-------------------------|------------------------------------|------------------------|
| GET    | `/users`                | Listar usuarios (+ filtros)        | 200                    |
| GET    | `/users?role=admin`     | Filtrar por rol                    | 200                    |
| GET    | `/users?is_active=true` | Filtrar por estado                 | 200                    |
| GET    | `/users/{user_id}`      | Consultar por id                   | 200 / 404              |
| POST   | `/users`                | Crear usuario                      | 201 / 400 / 422        |
| PUT    | `/users/{user_id}`      | Actualización completa             | 200 / 404 / 400 / 422  |
| PATCH  | `/users/{user_id}`      | Actualización parcial              | 200 / 404 / 400 / 422  |
| DELETE | `/users/{user_id}`      | Eliminar usuario (requiere API Key)| 204 / 404 / 401        |

Todas las respuestas incluyen las cabeceras `X-App-Name: device_systems` y
`X-API-Version: 1.0`.

## Códigos de estado usados

| Operación                | Método | Código                    |
|--------------------------|--------|---------------------------|
| Listar / consultar       | GET    | 200 OK                    |
| Crear                    | POST   | 201 Created               |
| Actualizar completo      | PUT    | 200 OK                    |
| Actualizar parcial       | PATCH  | 200 OK                    |
| Eliminar                 | DELETE | 204 No Content            |
| Usuario no encontrado    | *      | 404 Not Found             |
| Correo duplicado         | POST/PUT/PATCH | 400 Bad Request   |
| PATCH sin datos          | PATCH  | 400 Bad Request           |
| Datos inválidos          | *      | 422 Unprocessable Entity  |
| Sin API Key (DELETE)     | DELETE | 401 Unauthorized          |

## Ejemplos de peticiones y respuestas

### POST — crear usuario

```bash
curl -X POST http://127.0.0.1:8000/users \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Nuevo Usuario\", \"email\": \"nuevo@device.com\", \"role\": \"support\"}"
```

Respuesta **201**:

```json
{ "id": 4, "name": "Nuevo Usuario", "email": "nuevo@device.com", "role": "support", "is_active": true }
```

### PUT — reemplazo completo

```bash
curl -X PUT http://127.0.0.1:8000/users/4 \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Nombre Editado\", \"email\": \"nuevo@device.com\", \"role\": \"admin\", \"is_active\": false}"
```

Respuesta **200** con el usuario completo actualizado.

### PATCH — actualización parcial

```bash
curl -X PATCH http://127.0.0.1:8000/users/4 \
  -H "Content-Type: application/json" \
  -d "{\"role\": \"support\"}"
```

Respuesta **200**. Si el cuerpo va vacío (`{}`) → **400 Bad Request**.

### DELETE — eliminar (requiere API Key)

```bash
curl -X DELETE http://127.0.0.1:8000/users/4 \
  -H "X-API-Key: device-systems-2026"
```

Respuesta **204 No Content**. Sin la cabecera `X-API-Key` → **401 Unauthorized**.

## Manejo de errores implementado

La API controla los errores con `HTTPException`, devolviendo un mensaje claro:

```json
{ "detail": "Usuario no encontrado" }
```

Casos controlados:

- **Usuario no encontrado** → 404 (dependencia `get_user_or_404`).
- **Correo duplicado** (POST/PUT/PATCH) → 400.
- **Rol no permitido** → 422 (lo valida el enum `UserRole` de Pydantic).
- **PATCH sin datos** → 400.
- **Eliminar usuario inexistente** → 404.
- **DELETE sin API Key válida** → 401.
- **Datos inválidos** (nombre corto, email mal formado) → 422 automático de Pydantic.

## Uso de Dependency Injection (`Depends()`)

Las funciones reutilizables viven en `app/dependencies/user_dependencies.py` y se
inyectan en las rutas con `Depends()`:

- **`get_user_service()`** — provee el servicio de usuarios; evita crearlo a mano
  en cada endpoint.
- **`get_user_or_404(user_id)`** — busca un usuario y lanza 404 si no existe. Se
  **reutiliza en GET/{id}, PUT, PATCH y DELETE**, así el chequeo de existencia se
  escribe una sola vez.
- **`verify_api_key(x_api_key)`** — simula autenticación básica leyendo la
  cabecera `X-API-Key`; protege el endpoint DELETE.
- **`get_api_settings()`** — expone metadatos/configuración general de la API.

Ejemplo real (la ruta recibe el usuario ya validado por la dependencia):

```python
@router.get("/{user_id}", response_model=UserResponse)
def obtener_usuario(user: dict = Depends(get_user_or_404)):
    return user
```

## Documentación Swagger/OpenAPI

En `main.py` se configuran `title`, `description`, `version`, `contact` y
`openapi_tags`. Cada endpoint define `summary`, `description` y
`response_description`, y se agrupan con `tags=["Users"]`. Todo esto se ve en
`/docs` (Swagger UI) y `/redoc` (ReDoc) sin escribir documentación aparte.

## Pruebas

```bash
uv run pytest
```

18 pruebas automáticas cubren el CRUD completo y los escenarios de error
(404, 400, 401, 422). También se puede probar manualmente en Swagger UI,
Postman o Thunder Client.

## Capturas de Swagger UI y ReDoc

> Pegar aquí las capturas de la evidencia (ver instrucciones más abajo):
>
> - [ ] Swagger UI general (`/docs`)
> - [ ] ReDoc (`/redoc`)
> - [ ] GET /users y GET /users/{user_id}
> - [ ] POST /users
> - [ ] PUT /users/{user_id}
> - [ ] PATCH /users/{user_id}
> - [ ] DELETE /users/{user_id}
> - [ ] Errores controlados (404, 400 PATCH vacío, 401 sin API Key, 422)

## Reflexión final sobre la evolución del proyecto

El proyecto pasó de una API básica de GET/POST a una API REST profesional. Los
cambios principales fueron: (1) separar el código en capas (routes, services,
dependencies, data), lo que hace el proyecto más ordenado y fácil de mantener;
(2) completar el CRUD con PUT, PATCH y DELETE; (3) manejar errores de forma
consistente con `HTTPException` y los códigos HTTP correctos; (4) reutilizar
lógica con `Depends()`, evitando repetir el mismo código en cada endpoint; y
(5) mejorar la documentación automática con Swagger/OpenAPI. Esta evolución
muestra cómo una API crece hacia una estructura robusta, documentada y testeable.
