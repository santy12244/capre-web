import os
from datetime import timedelta
from flask import Flask
import config

# Constante para formateo de fechas (evita recrear en cada llamada)
MESES = ('ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN',
         'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC')


def create_app():
    app = Flask(__name__)
    app.secret_key = config.SECRET_KEY
    app.permanent_session_lifetime = timedelta(days=90)

    # Configuracion de cookies de sesion para evitar compartir entre dispositivos
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = not config.DEBUG  # Solo HTTPS en produccion
    app.config['SESSION_COOKIE_HTTPONLY'] = True

    # Limite de tamaño de archivos subidos
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

    # Cache de archivos estaticos por 1 año (en produccion)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000

    # Filtro para formatear fechas a DD/MES/AAAA (ej: 01/ENE/2024)
    @app.template_filter('fecha')
    def formato_fecha(value):
        if not value:
            return '—'
        try:
            partes = str(value).split('-')
            if len(partes) == 3:
                anio, mes, dia = partes
                return f"{dia}/{MESES[int(mes) - 1]}/{anio}"
            return value
        except:
            return value

    # Ensure required directories exist
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(config.DATA_FOLDER, exist_ok=True)

    # Make sessions permanent and generate unique device ID
    @app.before_request
    def setup_session():
        from flask import session
        import uuid
        session.permanent = True
        # Generar ID unico por dispositivo/navegador si no existe
        if 'device_id' not in session:
            session['device_id'] = str(uuid.uuid4())
            # Limpiar cualquier sesion activa heredada
            session.pop('active_session_id', None)

    # Headers de seguridad y cache
    @app.after_request
    def add_security_headers(response):
        # Headers de seguridad (siempre)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Evitar cache en respuestas HTML para que cada dispositivo tenga su sesion
        if response.content_type and 'text/html' in response.content_type:
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response

    # Manejador de error para archivos muy grandes
    @app.errorhandler(413)
    def file_too_large(e):
        from flask import flash, redirect, url_for
        flash('El archivo excede el tamaño maximo permitido (16 MB).', 'danger')
        return redirect(url_for('upload.upload_form'))

    # Manejador de errores generales (produccion)
    @app.errorhandler(500)
    def internal_error(e):
        from flask import render_template_string
        return render_template_string('''
            <!DOCTYPE html>
            <html><head><title>Error</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
            </head><body class="bg-light">
            <div class="container mt-5"><div class="alert alert-danger">
            <h4>Error del servidor</h4>
            <p>Ha ocurrido un error. Por favor intente nuevamente.</p>
            <a href="/" class="btn btn-primary">Volver al inicio</a>
            </div></div></body></html>
        '''), 500

    # Register blueprints
    from routes.main import bp as main_bp
    from routes.upload import bp as upload_bp
    from routes.principal import bp as principal_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(principal_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=config.DEBUG, port=5000)
