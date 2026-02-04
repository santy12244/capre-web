import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
EXPORT_FOLDER = os.path.join(BASE_DIR, 'exports')
DATA_FOLDER = os.path.join(BASE_DIR, 'data')

# SECRET_KEY: usar variable de entorno en produccion
# En produccion: set SECRET_KEY=tu-clave-segura-aqui (Windows)
# En produccion: export SECRET_KEY=tu-clave-segura-aqui (Linux)
SECRET_KEY = os.environ.get('SECRET_KEY', 'capre-dev-key-change-in-production')

# Modo de ejecucion
DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')

# Limite de tamaño de archivos (16 MB)
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
