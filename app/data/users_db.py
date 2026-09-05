"""Simulación de base de datos en memoria para el recurso `users`.

No hay un motor de base de datos real: los usuarios viven en esta lista
mientras el servidor esté encendido. Al reiniciar, vuelve a estos datos
sembrados. La capa de servicios (`user_service.py`) es la única que lee y
modifica esta lista; las rutas nunca la tocan directamente.
"""

# Cada usuario es un diccionario con la misma forma que el modelo UserResponse.
users_db: list[dict] = [
    {"id": 1, "name": "Juan Camilo Montes", "email": "juanca@device.com", "role": "admin", "is_active": True},
    {"id": 2, "name": "Ana Soporte", "email": "ana@device.com", "role": "support", "is_active": True},
    {"id": 3, "name": "Pedro Perez", "email": "pedro@device.com", "role": "user", "is_active": False},
]
