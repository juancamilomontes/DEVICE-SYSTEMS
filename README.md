# device_systems — API REST (v4.0 · Alembic, Relaciones y Joins)

**Actividad:** GA1-220501096-01-AA1-EV10 — FastAPI Avanzado (Proyecto Final v1)
**Autor:** Juan Camilo Montes
**Programa:** Análisis y Desarrollo de Software (ADSO) — SENA
**Rama de la entrega:** `device_systems_alembic_relaciones`

## Descripción

`device_systems` evoluciona de un CRUD de una sola tabla a un **sistema con relaciones**:
gestiona **usuarios**, **dispositivos** y **préstamos**. Incorpora **migraciones de
base de datos con Alembic**, **asociaciones entre modelos** (`ForeignKey` +
`relationship`) y **consultas con joins y filtros avanzados**.

- Un **usuario** puede tener muchos **préstamos** (One-to-Many).
- Un **dispositivo** puede aparecer en muchos préstamos históricos (One-to-Many).
- Cada **préstamo** pertenece a un usuario y a un dispositivo (Many-to-One).

## Tecnologías utilizadas

Python 3.11+ · **FastAPI** · **SQLAlchemy 2.0** · **Alembic** (migraciones) ·
**SQLite** · Uvicorn · Pydantic v2 · pytest · gestor **uv**.

## Estructura del proyecto

```
device_systems/
├── alembic/
│   ├── versions/            # migraciones generadas
│   └── env.py               # configurado con la metadata de los modelos
├── alembic.ini              # URL de la BD y configuración de Alembic
├── app/
│   ├── main.py              # crea la app y registra los 3 recursos
│   ├── database/connection.py
│   ├── models/              # user_model.py, device_model.py, loan_model.py
│   ├── schemas/             # user_schema.py, device_schema.py, loan_schema.py
│   ├── routes/              # user_routes.py, device_routes.py, loan_routes.py
│   ├── services/            # user_service.py, device_service.py, loan_service.py
│   └── dependencies/        # database_dependency.py, user_dependencies.py
├── requirements.txt
└── README.md
```

## Modelos y relaciones

| Modelo | Tabla | Campos clave | Relación |
|--------|-------|--------------|----------|
| `User` | users | id, name, email (único), role, is_active, created_at | `loans` → muchos préstamos |
| `Device` | devices | id, name, serial_number (único), device_type, brand, is_available, created_at | `loans` → muchos préstamos |
| `Loan` | loans | id, **user_id** (FK), **device_id** (FK), loan_date, return_date, status | `user`, `device` |

Las relaciones se definen con `relationship()` + `back_populates`, y las `ForeignKey`
garantizan la **integridad referencial** (un préstamo siempre apunta a un usuario y a
un dispositivo que existen).

## Instalación

```bash
uv sync          # o:  pip install -r requirements.txt
```

## Migraciones con Alembic

El esquema de la base de datos lo gestiona **Alembic** (no se crea a mano). Comandos:

```bash
# 1) inicializar Alembic (ya hecho, genera alembic/ y alembic.ini)
alembic init alembic

# 2) generar una migración a partir de los modelos
alembic revision --autogenerate -m "create users, devices and loans tables"

# 3) aplicar las migraciones (crea las tablas / el archivo device_systems.db)
alembic upgrade head

# 4) ver el historial de migraciones
alembic history
```

> Con `uv`, antepón `uv run` a cada comando (ej.: `uv run alembic upgrade head`).
> **Primero migra, luego arranca el servidor.**

## Ejecución del servidor

```bash
uv run uvicorn app.main:app --reload
```

Documentación: **Swagger** en `/docs` · **ReDoc** en `/redoc`.

## Endpoints

### Users
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST | `/users` | Listar (filtros) / crear |
| GET/PUT/PATCH/DELETE | `/users/{id}` | Consultar / actualizar / eliminar |
| GET | `/users/{id}/loans` | Préstamos del usuario (join) |

### Devices
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST | `/devices` | Listar (`?device_type=` `?is_available=` `?brand=` `?search=`) / crear |
| GET/PUT/PATCH/DELETE | `/devices/{id}` | Consultar / actualizar / eliminar |
| GET | `/devices/{id}/loans` | Historial de préstamos del dispositivo (join) |

### Loans
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/loans` | Listar (`?status=` `?user_email=` `?device_type=`) |
| GET | `/loans/details` | Listar con datos de usuario y dispositivo (join) |
| GET | `/loans/{id}` | Consultar un préstamo (con detalle) |
| POST | `/loans` | Registrar préstamo |
| PATCH | `/loans/{id}/return` | Devolver dispositivo |

## Reglas de negocio de los préstamos

**POST /loans**: valida que el usuario exista (404), que el dispositivo exista (404)
y que esté disponible (409); crea el préstamo y pone el dispositivo en
`is_available = False`.

**PATCH /loans/{id}/return**: valida que el préstamo exista (404) y que no esté ya
devuelto (409); marca `returned`, asigna `return_date` y pone el dispositivo en
`is_available = True`.

## Consultas con joins y filtros

`GET /loans/details` combina las tres tablas y devuelve la información relacionada:

```json
{
  "loan_id": 1,
  "status": "active",
  "user":   { "id": 1, "name": "Ana Pérez", "email": "ana@sena.edu.co" },
  "device": { "id": 3, "name": "Laptop Lenovo ThinkPad", "serial_number": "LEN-2024-001", "device_type": "laptop" }
}
```

Internamente se usan `join()`, `where()`/`filter()`, `ilike()` (búsqueda sin
distinguir mayúsculas) y `or_()` (búsqueda en varios campos).

## Códigos de estado

| Caso | Código |
|------|--------|
| Registro creado | 201 Created |
| Consulta / devolución | 200 OK |
| Eliminación | 204 No Content |
| Recurso no encontrado | 404 Not Found |
| Dato duplicado (email / serial) | 400 Bad Request |
| Regla de negocio (no disponible / ya devuelto) | 409 Conflict |
| Datos inválidos | 422 Unprocessable Entity |

## Pruebas

```bash
uv run pytest
```

23 pruebas automáticas (usuarios, dispositivos y préstamos) con base de datos en
memoria aislada; cubren el CRUD, las reglas de negocio, los joins y los filtros.

## Evidencias (capturas)

> Descomenta cada línea (quita `<!--` y `-->`) cuando agregues la imagen a `images/`.

### 1. `alembic init`
<!-- ![alembic init](images/alembic-init.png) -->

### 2. `alembic revision --autogenerate`
<!-- ![alembic revision](images/alembic-revision.png) -->

### 3. `alembic upgrade head`
<!-- ![alembic upgrade](images/alembic-upgrade.png) -->

### 4. Estructura de tablas generadas
<!-- ![tablas generadas](images/tablas-generadas.png) -->

### 5. Swagger UI (Users / Devices / Loans)
<!-- ![swagger ev10](images/swagger-ev10.png) -->

### 6. Crear usuario, dispositivo y préstamo
<!-- ![crear prestamo](images/crear-prestamo.png) -->

### 7. Consulta con joins (`/loans/details`)
<!-- ![joins](images/joins.png) -->

### 8. Filtros aplicados
<!-- ![filtros](images/filtros.png) -->

### 9. Devolución de dispositivo
<!-- ![devolucion](images/devolucion.png) -->

## Reflexión final

Las **migraciones con Alembic** permiten versionar la estructura de la base de datos:
cada cambio queda registrado y se aplica de forma controlada y reproducible, sin
perder datos ni tener que recrear tablas a mano. Las **relaciones entre modelos**
dan integridad al sistema (un préstamo no puede existir sin un usuario y un
dispositivo reales) y reflejan el dominio del problema. Las **consultas con joins y
filtros** convierten datos separados en información útil —qué usuario tiene qué
dispositivo, qué préstamos están activos, el historial de un equipo— que es,
finalmente, lo que hace valioso a un backend.

---

📘 Guía de estudio visual del proyecto (EV07 → EV09): `guia_estudio.html`
