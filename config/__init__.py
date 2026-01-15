# __init__.py

# Importa la instancia de la aplicación Celery para que se cargue
# cuando Django se inicie. Esto asegura que la aplicación Celery
# esté disponible para todos los módulos que la necesiten.
from .celery import app as celery_app

__all__ = ('celery_app',)