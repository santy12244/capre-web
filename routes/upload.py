import os
import zipfile
import tempfile
import shutil
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
import config
from services.file_utils import validate_upload_set, detect_table_number
from services.dbf_import import import_dbf_files
from services.dbf_export import export_all_tables
from models.database import set_session_device, session_exists_by_prefix

bp = Blueprint('upload', __name__)


@bp.route('/upload')
def upload_form():
    return render_template('upload.html')


@bp.route('/upload', methods=['POST'])
def upload_files():
    files = request.files.getlist('dbf_files')

    if not files or len(files) != 3:
        flash('Debe seleccionar exactamente 3 archivos .dbf', 'danger')
        return redirect(url_for('upload.upload_form'))

    # Check all files have content
    filenames = []
    for f in files:
        if not f.filename or not f.filename.lower().endswith('.dbf'):
            flash('Todos los archivos deben ser de tipo .dbf', 'danger')
            return redirect(url_for('upload.upload_form'))
        filenames.append(f.filename)

    # Validate file set
    try:
        prefix_code = validate_upload_set(filenames)
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('upload.upload_form'))

    # Verificar si ya existe una sesion con este codigo de hato
    device_id = session.get('device_id')
    exists, farm_name = session_exists_by_prefix(prefix_code, device_id=device_id)
    if exists:
        flash(f'Ya existe una sesion con el codigo de hato "{prefix_code}" ({farm_name}). Elimine la sesion existente antes de importar.', 'danger')
        return redirect(url_for('upload.upload_form'))

    # Save files temporarily
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    file_paths = {}
    saved_paths = []

    try:
        for f in files:
            table_num = detect_table_number(f.filename)
            save_path = os.path.join(config.UPLOAD_FOLDER, f.filename)
            f.save(save_path)
            file_paths[table_num] = save_path
            saved_paths.append(save_path)

        # Import into SQLite
        session_id, counts = import_dbf_files(file_paths, prefix_code)

        # Asociar sesion con el dispositivo actual
        device_id = session.get('device_id')
        if device_id:
            set_session_device(session_id, device_id)

        # Set as active session
        session['active_session_id'] = session_id

        flash(
            f'Importacion exitosa: {counts["farm_name"]} - '
            f'Tabla1: {counts["tabla1"]} reg, '
            f'Tabla2: {counts["tabla2"]} reg, '
            f'Tabla3: {counts["tabla3"]} reg',
            'success'
        )
        return redirect(url_for('main.index'))

    except Exception as e:
        flash(f'Error al importar: {str(e)}', 'danger')
        return redirect(url_for('upload.upload_form'))

    finally:
        # Clean up uploaded files
        for path in saved_paths:
            if os.path.exists(path):
                os.remove(path)


@bp.route('/export')
def export_files():
    """Export the 3 tables as DBF files in a ZIP."""
    session_id = session.get('active_session_id')
    if not session_id:
        flash('No hay sesion activa para exportar.', 'danger')
        return redirect(url_for('main.index'))

    # Create temporary directory for export
    temp_dir = tempfile.mkdtemp()

    try:
        # Export tables to DBF
        result = export_all_tables(session_id, temp_dir)
        prefix = result['prefix']
        farm_name = result['farm_name']

        # Create ZIP file in memory
        import io
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(result['tabla1'], os.path.basename(result['tabla1']))
            zipf.write(result['tabla2'], os.path.basename(result['tabla2']))
            zipf.write(result['tabla3'], os.path.basename(result['tabla3']))

        zip_buffer.seek(0)

        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)

        # Send file for download
        zip_filename = f'{prefix}_{farm_name}.zip'
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )

    except Exception as e:
        # Clean up on error
        shutil.rmtree(temp_dir, ignore_errors=True)
        flash(f'Error al exportar: {str(e)}', 'danger')
        return redirect(url_for('principal.index'))
