# device_systems — API REST de Usuarios

**Actividad:** GA1-220501096-01-AA1-EV07 — Fundamentos de FastAPI
**Autor:** Juan Camilo Montes
**Programa:** Análisis y Desarrollo de Software (ADSO) — SENA

## Descripción

`device_systems` es una API REST construida con **FastAPI** para administrar
el recurso **usuarios** del sistema. Permite listar, consultar por id, filtrar
y registrar usuarios, aplicando:

- Validación de datos con **Pydantic v2** (nombre, correo, rol, estado).
- **Path Parameters** (`/users/{user_id}`) y **Query Parameters** (`?role=`, `?is_active=`).
- **Response Models** para estandarizar la salida.
- **Cabeceras HTTP personalizadas** (`X-App-Name`, `X-API-Version`).

> Nota: por ser una actividad de fundamentos, los usuarios se guardan en una
> lista **en memoria** (no hay base de datos). Los datos se reinician cada vez
> que se reinicia el servidor.

## Modelo de Usuario

| Campo       | Tipo    | Validación                                      |
|-------------|---------|-------------------------------------------------|
| `id`        | int     | Lo asigna el servidor (no se envía al crear)    |
| `name`      | str     | Obligatorio, mínimo 3 caracteres                |
| `email`     | EmailStr| Formato de correo válido y único                |
| `role`      | enum    | Solo: `admin`, `support`, `user` (default `user`)|
| `is_active` | bool    | Default `true`                                  |

## Instalación de dependencias

El proyecto usa el gestor [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
```

Esto instala FastAPI, Uvicorn, Pydantic (con `email-validator`) y las
dependencias de desarrollo (pytest, httpx).

## Ejecución del servidor

```bash
uv run uvicorn app.main:app --reload
```

El servidor queda disponible en:

- API: http://127.0.0.1:8000
- **Swagger UI**: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Tabla de endpoints

| Método | Ruta                     | Descripción                                  | Respuesta |
|--------|--------------------------|----------------------------------------------|-----------|
| GET    | `/`                      | Mensaje de bienvenida                        | 200       |
| GET    | `/estado`                | Estado de la aplicación                      | 200       |
| GET    | `/users`                 | Lista todos los usuarios                     | 200       |
| GET    | `/users?role=admin`      | Filtra usuarios por rol                      | 200       |
| GET    | `/users?is_active=true`  | Filtra usuarios por estado activo            | 200       |
| GET    | `/users/{user_id}`       | Consulta un usuario por id                   | 200 / 404 |
| POST   | `/users`                 | Registra un nuevo usuario                    | 201 / 409 / 422 |

Todas las respuestas incluyen las cabeceras:

```
X-App-Name: device_systems
X-API-Version: 1.0
```

## Ejemplos de peticiones

### GET — listar todos los usuarios

```bash
curl http://127.0.0.1:8000/users
```

```json
[
  {"id": 1, "name": "Juan Camilo Montes", "email": "juanca@device.com", "role": "admin", "is_active": true},
  {"id": 2, "name": "Ana Soporte", "email": "ana@device.com", "role": "support", "is_active": true},
  {"id": 3, "name": "Pedro Perez", "email": "pedro@device.com", "role": "user", "is_active": false}
]
```

### GET — filtrar por rol (Query Parameter)

```bash
curl "http://127.0.0.1:8000/users?role=admin"
```

### GET — consultar por id (Path Parameter)

```bash
curl http://127.0.0.1:8000/users/2
```

Si el id no existe, devuelve **404**:

```json
{ "detail": "No existe un usuario con id 999" }
```

### POST — registrar un usuario

```bash
curl -X POST http://127.0.0.1:8000/users \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Nuevo Usuario\", \"email\": \"nuevo@device.com\", \"role\": \"support\"}"
```

Respuesta **201**:

```json
{ "id": 4, "name": "Nuevo Usuario", "email": "nuevo@device.com", "role": "support", "is_active": true }
```

### Validaciones y errores

| Caso                       | Código | Motivo                                   |
|----------------------------|--------|------------------------------------------|
| Correo repetido            | 409    | El correo ya está registrado             |
| `name` con menos de 3 car. | 422    | No cumple `min_length=3`                 |
| Correo con formato inválido| 422    | `EmailStr` rechaza el valor              |
| `role` fuera del enum      | 422    | Solo se permite `admin`/`support`/`user` |

## Pruebas

Pruebas automáticas con pytest (10 casos):

```bash
uv run pytest
```

También se puede probar manualmente desde **Swagger UI** (`/docs`), Postman o
Thunder Client.

## Capturas de Swagger UI

> Pegar aquí las capturas de pantalla solicitadas por la evidencia:
>
> - [ ] Vista general de Swagger UI (`/docs`)
> - [ ] `GET /users`
> - [ ] `GET /users/{user_id}`
> - [ ] `POST /users`
> - [ ] Evidencia de validaciones / errores (422, 404, 409)

## Reflexión sobre el uso de FastAPI

FastAPI permite construir APIs REST de forma rápida y segura: la validación de
datos con Pydantic v2 se declara directamente en los modelos, la documentación
interactiva (Swagger UI) se genera sola a partir del código, y los tipos de
Python sirven a la vez como validación y como contrato de la API. Separar el
proyecto en `schemas` (modelos) y `routes` (endpoints) mantiene el código
ordenado y fácil de mantener.
