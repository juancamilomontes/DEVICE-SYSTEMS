"""Dependencia que entrega una sesión de base de datos a los endpoints.

FastAPI llama a `get_db()` en cada petición que la use con `Depends(get_db)`:
abre una sesión, la "presta" (yield) al endpoint, y al terminar la CIERRA
siempre (aunque haya error), gracias al try/finally.
"""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.database.connection import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Abre una sesión, la entrega al endpoint y la cierra al final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
