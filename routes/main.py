from flask import Blueprint, render_template, redirect, url_for, flash, session, make_response, request, jsonify
from models.database import list_sessions, delete_session

bp = Blueprint('main', __name__)


@bp.route('/api/restore-device', methods=['POST'])
def restore_device():
    """Restaura el device_id desde localStorage cuando la cookie se perdio."""
    data = request.get_json(silent=True)
    if not data or not data.get('device_id'):
        return jsonify({'ok': False}), 400
    stored_device_id = data['device_id']
    # Verificar que el device_id existe en al menos una sesion en el servidor
    sessions = list_sessions(device_id=stored_device_id)
    if sessions:
        session['device_id'] = stored_device_id
        session.modified = True
        return jsonify({'ok': True, 'restored': True})
    return jsonify({'ok': False, 'restored': False}), 404


@bp.route('/')
def index():
    device_id = session.get('device_id')
    # Filtrar sesiones: solo mostrar las de este dispositivo
    sessions = list_sessions(device_id=device_id)
    active_session = session.get('active_session_id')
    device_id_short = device_id[:8] if device_id else 'desconocido'
    response = make_response(render_template(
        'index.html',
        sessions=sessions,
        active_session=active_session,
        device_id=device_id_short
    ))
    return response


@bp.route('/session/<session_id>/select')
def select_session(session_id):
    session['active_session_id'] = session_id
    session.modified = True  # Forzar guardar la sesion
    flash('Sesion activada correctamente.', 'success')
    return redirect(url_for('principal.index'))


@bp.route('/session/<session_id>/delete', methods=['POST'])
def remove_session(session_id):
    if session.get('active_session_id') == session_id:
        session.pop('active_session_id', None)
    delete_session(session_id)
    flash('Sesion eliminada.', 'info')
    return redirect(url_for('main.index'))
