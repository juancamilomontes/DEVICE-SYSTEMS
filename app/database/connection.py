"""Conexión con la base de datos usando SQLAlchemy.

Aquí se configuran las 3 piezas base de SQLAlchemy:
- engine: el "motor" que sabe hablar con la base de datos concreta (SQLite).
- SessionLocal: fábrica de sesiones (cada petición abre una y la cierra).
- Base: clase padre de la que heredan los modelos (las tablas).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Cadena de conexión. Para desarrollo usamos SQLite: un archivo local .db.
# Si mañana se cambia a PostgreSQL, solo se cambia esta línea.
DATABASE_URL = "sqlite:///./device_systems.db"

# El engine es la conexión de bajo nivel con la base de datos.
# connect_args={"check_same_thread": False} es EXCLUSIVO de SQLite: permite que
# la misma conexión se use desde distintos hilos (FastAPI lo necesita).
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# SessionLocal es una FÁBRICA de sesiones. Cada sesión es como una "conversación"
# con la base de datos donde se hacen consultas y cambios.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base es la clase declarativa: todos los modelos (tablas) heredarán de ella.
Base = declarative_base()
