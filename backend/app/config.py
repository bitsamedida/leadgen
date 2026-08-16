"""
Configuración centralizada. Todo lo que pueda cambiar entre entornos
(API keys, ruta de la DB) vive aquí y se lee de variables de entorno,
nunca hardcodeado en el resto del código.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = os.getenv("LEADGEN_DB_PATH", str(BASE_DIR / "leadgen.db"))

# Fuentes externas — cada conector lee aquí su propia key.
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")

# Cuántos leads se re-verifican por corrida del proceso de refresco.
REFRESH_BATCH_SIZE = int(os.getenv("REFRESH_BATCH_SIZE", "50"))

# A partir de cuántos intentos fallidos de verificación seguidos
# se marca un lead como inactivo en vez de seguir reintentando.
MAX_VERIFICATION_ATTEMPTS = int(os.getenv("MAX_VERIFICATION_ATTEMPTS", "3"))
