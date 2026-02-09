import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
EXPORT_FOLDER = os.path.join(BASE_DIR, 'exports')
DATA_FOLDER = os.path.join(BASE_DIR, 'data')

# SECRET_KEY: se genera automaticamente y se guarda en archivo para persistencia.
# Si el archivo no existe, se crea uno nuevo. Esto evita que reinicios del servidor
# invaliden las cookies de sesion de los usuarios.
_SECRET_KEY_FILE = os.path.join(BASE_DIR, 'data', '.secret_key')


def _get_or_create_secret_key():
    """Obtiene o genera un SECRET_KEY persistente guardado en archivo."""
    # Prioridad: variable de entorno > archivo persistente > generar nuevo
    env_key = os.environ.get('SECRET_KEY')
    if env_key:
        return env_key
    os.makedirs(os.path.dirname(_SECRET_KEY_FILE), exist_ok=True)
    if os.path.exists(_SECRET_KEY_FILE):
        with open(_SECRET_KEY_FILE, 'r') as f:
            return f.read().strip()
    import secrets
    new_key = secrets.token_hex(32)
    with open(_SECRET_KEY_FILE, 'w') as f:
        f.write(new_key)
    return new_key


SECRET_KEY = _get_or_create_secret_key()

# Modo de ejecucion
DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')

# Limite de tamaño de archivos (16 MB)
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
