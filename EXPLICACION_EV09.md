# Explicación paso a paso — EV09 (Persistencia con SQLAlchemy)

Documento de estudio. Explica **qué se hizo, por qué, y cómo funciona** cada
pieza, pensado para entenderlo desde cero (primera vez con SQLAlchemy).

---

## 1. La idea general (el "antes" y el "después")

**Antes (EV07/EV08):** los usuarios se guardaban en una **lista de Python en
memoria**. Problema: cuando apagas el servidor, la lista se borra. Los datos
no son permanentes.

**Ahora (EV09):** los usuarios se guardan en una **base de datos** (un archivo
`device_systems.db` de SQLite). Los datos **quedan guardados** aunque reinicies.

Para hablar con la base de datos usamos **SQLAlchemy**, que es un **ORM**.

### ¿Qué es un ORM?

ORM = *Object Relational Mapper* (Mapeador Objeto-Relacional). Es un traductor:
te deja trabajar con **objetos y clases de Python** en vez de escribir SQL a mano.

- Tú escribes: `db.query(User).filter(User.id == 5).first()`
- SQLAlchemy traduce eso a SQL: `SELECT * FROM users WHERE id = 5 LIMIT 1;`

Ventaja: programas en Python normal, sin mezclar cadenas de SQL, y si cambias de
base de datos (SQLite → PostgreSQL) casi no tocas código.

---

## 2. Las 3 piezas base de SQLAlchemy (`app/database/connection.py`)

Todo empieza aquí. Hay 3 objetos fundamentales:

```python
DATABASE_URL = "sqlite:///./device_systems.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

- **`engine`**: el "motor" de conexión. Sabe *cómo* conectarse a la base de datos
  concreta (aquí, un archivo SQLite). Es de bajo nivel; casi nunca lo usas directo.
- **`SessionLocal`**: una **fábrica de sesiones**. Una *sesión* es como una
  "conversación" con la base de datos: por ahí haces consultas y guardas cambios.
  Se abre una por cada petición y se cierra al terminar.
- **`Base`**: la clase padre de la que heredan **todos los modelos** (tablas).
  SQLAlchemy usa `Base` para saber qué tablas existen.

> `check_same_thread=False` es **solo para SQLite**: permite usar la conexión
> desde varios hilos, que es como funciona FastAPI. Con PostgreSQL se quita.

---

## 3. El modelo SQLAlchemy = la tabla (`app/models/user_model.py`)

Este archivo define **cómo es la tabla `users`** en la base de datos:

```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    role = Column(String, nullable=False, default="user")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

- Hereda de `Base` → SQLAlchemy la reconoce como una tabla.
- `__tablename__` = nombre real de la tabla.
- Cada `Column(...)` = una columna. Los **constraints** (restricciones) son:
  - `primary_key=True` → identificador único de cada fila (se autoincrementa).
  - `nullable=False` → obligatorio, no puede quedar vacío.
  - `unique=True` → no puede repetirse (por eso no hay dos correos iguales; esto
    lo garantiza la **base de datos**, no solo Python).
  - `default=...` → valor por defecto si no se envía.
  - `index=True` → crea un índice para que las búsquedas por esa columna sean
    rápidas.
- `created_at` se rellena solo con la fecha/hora actual al insertar.

**Una fila de la tabla = una instancia de `User`.**

---

## 4. Los schemas Pydantic = el contrato de la API (`app/schemas/user_schema.py`)

Los schemas validan el **JSON** que entra y define el que sale. Hay 4:

| Schema         | Para qué          | Campos                              |
|----------------|-------------------|-------------------------------------|
| `UserCreate`   | POST (crear)      | name, email, role, is_active        |
| `UserUpdate`   | PUT (reemplazo)   | name, email, role, is_active (todos)|
| `UserPatch`    | PATCH (parcial)   | todos **opcionales**                |
| `UserResponse` | respuesta         | + `id` y `created_at`               |

Validaciones (las hace Pydantic automáticamente):
- `name`: mínimo 3 caracteres (`min_length=3`).
- `email`: formato válido (`EmailStr`).
- `role`: solo `admin`, `support`, `user` (un `Enum`).

En `UserResponse` está la línea clave:

```python
model_config = ConfigDict(from_attributes=True)
```

Esto permite crear el schema **directo desde un objeto SQLAlchemy** (leyendo
`user.id`, `user.name`, ...). Sin eso, habría que pasarle un diccionario a mano.

### ⭐ Diferencia modelo SQLAlchemy vs schema Pydantic (pregunta de la guía)

- **Modelo SQLAlchemy** = cómo se **guarda** en la base de datos (tabla, columnas,
  constraints SQL). Vive en `models/`.
- **Schema Pydantic** = cómo **entra/sale** por la API (validación del JSON).
  Vive en `schemas/`.

Son distintos a propósito: así la API valida datos y controla qué expone, sin
quedar "pegada" a la estructura interna de la base de datos.

---

## 5. La dependencia de base de datos (`app/dependencies/database_dependency.py`)

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Esta función abre una sesión, la **presta** (`yield`) al endpoint, y **siempre la
cierra** al final (el `finally` corre aunque haya error). FastAPI la conecta a los
endpoints con `Depends(get_db)`: en cada petición te da una sesión fresca.

> `yield` (no `return`): permite ejecutar código *después* de que el endpoint
> termina (cerrar la sesión). Es un patrón típico de dependencias en FastAPI.

---

## 6. El servicio CRUD (`app/services/user_service.py`)

Aquí están las operaciones reales contra la base de datos. Todas reciben `db`
(la sesión). Ejemplo de crear:

```python
def create_user(db, data):
    nuevo = User(name=data.name, email=data.email, role=data.role.value, is_active=data.is_active)
    db.add(nuevo)       # 1. marca el objeto para insertar
    db.commit()         # 2. confirma -> INSERT real en la base de datos
    db.refresh(nuevo)   # 3. recarga el objeto con el id y created_at generados
    return nuevo
```

Los 3 verbos que más vas a usar:
- **`db.add(obj)`** → agrega un objeto nuevo (para insertar).
- **`db.commit()`** → confirma los cambios (los escribe de verdad en la BD).
- **`db.refresh(obj)`** → vuelve a leer el objeto desde la BD (para traer valores
  que genera ella, como el `id`).
- **`db.delete(obj)`** → marca para borrar (luego `commit`).

Y para **consultar**:
- `db.query(User)` → empieza una consulta sobre la tabla.
- `.filter(User.role == "admin")` → agrega un WHERE.
- `.order_by(...)` → ordena.
- `.first()` → trae el primero (o `None`). `.all()` → trae todos (lista).

Funciones implementadas: crear, listar (con filtros y orden), buscar por id,
buscar por email, PUT (reemplazo completo), PATCH (parcial), eliminar.

---

## 7. Las rutas (`app/routes/user_routes.py`)

Los endpoints son "delgados": reciben la sesión, validan reglas y llaman al
servicio. Ejemplo de crear:

```python
@router.post("", response_model=UserResponse, status_code=201)
def crear_usuario(datos: UserCreate, db: Session = Depends(get_db)):
    if user_service.get_user_by_email(db, datos.email):
        raise HTTPException(400, f"El correo {datos.email} ya está registrado")
    return user_service.create_user(db, datos)
```

Fíjate:
- `datos: UserCreate` → Pydantic valida el JSON de entrada (si algo está mal, 422
  automático).
- `db: Session = Depends(get_db)` → FastAPI inyecta la sesión.
- Se revisa email duplicado → si existe, `HTTPException(400)`.
- `response_model=UserResponse` → la salida se convierte a ese schema (agrega id y
  created_at, oculta lo que no esté ahí).

Otra dependencia reutilizada es **`get_user_or_404`**: busca el usuario por id y,
si no existe, lanza 404. La usan GET/{id}, PUT, PATCH y DELETE, así ese chequeo se
escribe una sola vez.

---

## 8. El arranque (`app/main.py`)

Dos cosas nuevas importantes:

```python
Base.metadata.create_all(bind=engine)   # crea las tablas si no existen
```

Esto lee todos los modelos que heredan de `Base` y **crea las tablas** en la base
de datos. Con SQLite, la primera vez genera el archivo `device_systems.db`.

También hay un **sembrado inicial**: si la tabla está vacía, inserta 3 usuarios de
ejemplo (para que los GET muestren algo la primera vez). Como ahora es
persistente, en los siguientes arranques ya hay datos y no se vuelve a sembrar.

---

## 9. El recorrido completo de una petición (ejemplo: crear usuario)

1. El cliente envía `POST /users` con un JSON.
2. **Pydantic** (`UserCreate`) valida el JSON. Si está mal → **422**.
3. FastAPI abre una sesión con **`get_db`** y la inyecta.
4. La ruta pregunta al **servicio** si el email ya existe. Si sí → **400**.
5. El servicio crea un objeto **SQLAlchemy** `User`, hace `add` + `commit`.
6. La base de datos genera el `id` y `created_at`; `refresh` los trae.
7. FastAPI convierte el objeto a **`UserResponse`** y responde **201** con el JSON.
8. La sesión se **cierra** (el `finally` de `get_db`).

---

## 10. Por qué importa la persistencia (resumen para exponer)

- Los datos **no se pierden** al reiniciar el servidor.
- La base de datos **garantiza integridad** con constraints (ej.: `unique` en
  email impide duplicados de verdad, no solo con un `if` en Python).
- El código queda **ordenado en capas**: conexión, modelo, schema, servicio, ruta.
- Separar **modelo (BD)** de **schema (API)** hace el proyecto flexible: podrías
  cambiar la base de datos sin reescribir la API.

---

## 11. Preguntas rápidas para autoevaluarte

1. ¿Qué diferencia hay entre el modelo `User` (SQLAlchemy) y `UserResponse`
   (Pydantic)?
2. ¿Para qué sirve `db.commit()`? ¿Y `db.refresh()`?
3. ¿Por qué `get_db` usa `yield` en vez de `return`?
4. ¿Qué constraint impide dos usuarios con el mismo correo, y en qué archivo está?
5. ¿Qué hace `Base.metadata.create_all(bind=engine)` y dónde se llama?
6. Si quisieras pasar de SQLite a PostgreSQL, ¿qué línea cambiarías?
