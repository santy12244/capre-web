from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session as flask_session, jsonify
from models.database import get_db

bp = Blueprint('principal', __name__)


def _get_session_id():
    return flask_session.get('active_session_id')


@bp.route('/principal')
def index():
    session_id = _get_session_id()
    if not session_id:
        flash('Debe seleccionar una sesion de trabajo primero.', 'warning')
        return redirect(url_for('main.index'))

    conn = get_db(session_id)

    # Load farm info (tabla1)
    hato = conn.execute('SELECT * FROM tabla1 LIMIT 1').fetchone()

    # Load animal list from tabla2 for navigation
    animales = conn.execute(
        'SELECT id, codint, orejera, nombre FROM tabla2 ORDER BY nombre'
    ).fetchall()

    # Current animal index
    animal_idx = request.args.get('idx', 0, type=int)
    animal = None
    if animales:
        if animal_idx < 0:
            animal_idx = 0
        if animal_idx >= len(animales):
            animal_idx = len(animales) - 1
        animal_id = animales[animal_idx]['id']
        animal = conn.execute('SELECT * FROM tabla2 WHERE id = ?', (animal_id,)).fetchone()

    # Active tab
    tab = request.args.get('tab', 'servicios')

    conn.close()

    # Date limits for novelty fields
    fecha_min = hato['fecultprb'] or '' if hato else ''
    fecha_max = hato['fecprbact'] or '' if hato else ''

    # Calcular fecha minima para servicios (125 dias antes de fecha de validacion)
    fecha_min_servicio = ''
    if fecha_max:
        try:
            fec_val = datetime.strptime(fecha_max, '%Y-%m-%d')
            fec_min_ser = fec_val - timedelta(days=125)
            fecha_min_servicio = fec_min_ser.strftime('%Y-%m-%d')
        except ValueError:
            fecha_min_servicio = fecha_min

    return render_template(
        'principal.html',
        hato=hato,
        animales=animales,
        animal=animal,
        animal_idx=animal_idx,
        total_animales=len(animales),
        tab=tab,
        fecha_min=fecha_min,
        fecha_max=fecha_max,
        fecha_min_servicio=fecha_min_servicio,
    )


@bp.route('/principal/api/animal/<int:idx>')
def api_get_animal(idx):
    """API para obtener datos del animal via AJAX."""
    session_id = _get_session_id()
    if not session_id:
        return jsonify({'success': False, 'error': 'Sin sesión activa'}), 401

    conn = get_db(session_id)

    # Load animal list from tabla2
    animales = conn.execute(
        'SELECT id, codint, orejera, nombre FROM tabla2 ORDER BY nombre'
    ).fetchall()

    if not animales:
        conn.close()
        return jsonify({'success': False, 'error': 'No hay animales'}), 404

    # Validate index
    if idx < 0:
        idx = 0
    if idx >= len(animales):
        idx = len(animales) - 1

    animal_id = animales[idx]['id']
    animal_row = conn.execute('SELECT * FROM tabla2 WHERE id = ?', (animal_id,)).fetchone()
    conn.close()

    # Convert to dict
    animal = dict(animal_row)

    # Format dates for display
    def format_fecha(fecha_str):
        if not fecha_str:
            return '—'
        try:
            meses = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC']
            d = datetime.strptime(fecha_str, '%Y-%m-%d')
            return f"{d.day:02d}/{meses[d.month-1]}/{d.year}"
        except:
            return fecha_str or '—'

    # Estado mapping
    estado_map = {'0': 'Ternera', '1': 'Vaca parida', '2': 'Novilla parida', '3': 'Ing. seca', '4': 'Ing. produccion', '5': 'Aborto', '6': 'Seca'}
    estado_color = {'0': 'secondary', '1': 'success', '2': 'success', '3': 'warning', '4': 'info', '5': 'danger', '6': 'dark'}
    est = str(animal.get('estado', ''))

    # PAC mapping
    pac_val = str(animal.get('pac', '')).upper().strip()
    pac_map = {'A': 'Abierta', 'P': 'Preñada'}
    pac_color = {'A': 'danger', 'P': 'success'}

    return jsonify({
        'success': True,
        'animal_idx': idx,
        'total_animales': len(animales),
        'animal': {
            'id': animal['id'],
            'orejera': animal.get('orejera', ''),
            'nombre': animal.get('nombre', ''),
            'codint': animal.get('codint', ''),
            'registro': animal.get('registro') or '—',
            'estado': estado_map.get(est, est or '—'),
            'estado_color': estado_color.get(est, 'info'),
            'diagnostico': pac_map.get(pac_val, '') if pac_val else '',
            'diagnostico_color': pac_color.get(pac_val, 'secondary'),
            'ultlec': animal.get('ultlec') or '—',
            'dialec': animal.get('dialec') or '—',
            'numser': animal.get('numser') or '0',
            'fecultser': format_fecha(animal.get('fecultser')),
            'toro': animal.get('codtor') or animal.get('toro') or '—',
            'clasi': animal.get('clasi') or '—',
            'ptos': animal.get('ptos') or '',
            'fecest': format_fecha(animal.get('fecest')),
            # Raw values for forms
            'fecser_raw': animal.get('fecser') or '',
            'toro_raw': animal.get('toro') or '',
            'calor': animal.get('calor') or '',
            'fecseca_raw': animal.get('fecseca') or '',
            'fecchp_raw': animal.get('fecchp') or '',
            'panew': animal.get('panew') or '',
            'pac': animal.get('pac') or '',
            'fecparto_raw': animal.get('fecparto') or '',
            'tipoparto': animal.get('tipoparto') or '',
            'hacer1': animal.get('hacer1') or '',
            'orecria1': animal.get('orecria1') or '',
            'nomcria1': animal.get('nomcria1') or '',
            'sexcria1': animal.get('sexcria1') or '',
            'hacer2': animal.get('hacer2') or '',
            'orecria2': animal.get('orecria2') or '',
            'nomcria2': animal.get('nomcria2') or '',
            'sexcria2': animal.get('sexcria2') or '',
            'fecsale_raw': animal.get('fecsale') or '',
            'motsale': animal.get('motsale') or '',
            'cart': animal.get('cart') or '',
            'fecultser_raw': animal.get('fecultser') or '',
        }
    })


@bp.route('/principal/ordenos')
def ordenos_grupal():
    """Vista grupal de ordeños para animales en producción."""
    session_id = _get_session_id()
    if not session_id:
        return redirect(url_for('main.index'))

    conn = get_db(session_id)
    hato = conn.execute('SELECT * FROM tabla1 LIMIT 1').fetchone()

    # Validar que exista fecha de validacion
    if not hato or not hato['fecprbact']:
        conn.close()
        flash('Debe ingresar la Fecha de Validacion antes de acceder a Ordeños.', 'warning')
        return redirect(url_for('principal.index'))

    # Obtener parámetro de ordenamiento
    orden = request.args.get('orden', 'nombre_asc')
    opciones_validas = ('nombre_asc', 'nombre_desc', 'orejera_asc', 'orejera_desc')
    if orden not in opciones_validas:
        orden = 'nombre_asc'

    # Definir la cláusula ORDER BY según el tipo de ordenamiento
    order_map = {
        'nombre_asc': 'nombre ASC',
        'nombre_desc': 'nombre DESC',
        'orejera_asc': 'CAST(orejera AS INTEGER) ASC',
        'orejera_desc': 'CAST(orejera AS INTEGER) DESC',
    }
    order_clause = order_map.get(orden, 'nombre ASC')

    # Animales en estado 1, 2 o con parto registrado, EXCLUYENDO los que tienen salida reportada
    animales = conn.execute(f'''
        SELECT id, codint, orejera, nombre, estado, fecest, fecparto, dialec, ultlec, ord1, ord2, ord3
        FROM tabla2
        WHERE (estado IN ('1', '2') OR fecparto IS NOT NULL) AND fecsale IS NULL
        ORDER BY {order_clause}
    ''').fetchall()
    conn.close()

    return render_template('ordenos_grupal.html', hato=hato, animales=animales, orden=orden)


@bp.route('/principal/ordenos/guardar', methods=['POST'])
def guardar_ordenos_grupal():
    """Guardar ordeños de múltiples animales."""
    session_id = _get_session_id()
    if not session_id:
        return redirect(url_for('main.index'))

    conn = get_db(session_id)

    # Validar que exista fecha de validacion
    hato = conn.execute('SELECT fecprbact FROM tabla1 LIMIT 1').fetchone()
    if not hato or not hato['fecprbact']:
        conn.close()
        flash('Debe ingresar la Fecha de Validacion antes de guardar ordeños.', 'warning')
        return redirect(url_for('principal.index'))

    # Obtener todos los IDs de animales del formulario
    animal_ids = request.form.getlist('animal_id')

    for animal_id in animal_ids:
        ord1 = request.form.get(f'ord1_{animal_id}', '').strip()
        ord2 = request.form.get(f'ord2_{animal_id}', '').strip()
        ord3 = request.form.get(f'ord3_{animal_id}', '').strip()

        ord1_val = float(ord1) if ord1 else None
        ord2_val = float(ord2) if ord2 else None
        ord3_val = float(ord3) if ord3 else None

        conn.execute(
            'UPDATE tabla2 SET ord1=?, ord2=?, ord3=? WHERE id=?',
            (ord1_val, ord2_val, ord3_val, animal_id)
        )

    conn.commit()
    conn.close()

    flash('Ordeños guardados correctamente.', 'success')
    return redirect(url_for('principal.ordenos_grupal'))


@bp.route('/principal/ordenos/auto-guardar', methods=['POST'])
def auto_guardar_ordeno():
    """Auto-guardar un ordeño individual via AJAX."""
    session_id = _get_session_id()
    if not session_id:
        return jsonify({'success': False, 'error': 'Sin sesión activa'}), 401

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Datos no válidos'}), 400

    animal_id = data.get('animal_id')
    campo = data.get('campo')  # ord1, ord2, ord3
    valor = data.get('valor')

    if not animal_id or campo not in ('ord1', 'ord2', 'ord3'):
        return jsonify({'success': False, 'error': 'Parámetros inválidos'}), 400

    try:
        valor_float = float(valor) if valor and valor.strip() else None
    except ValueError:
        return jsonify({'success': False, 'error': 'Valor no numérico'}), 400

    conn = get_db(session_id)

    # Validar que exista fecha de validacion
    hato = conn.execute('SELECT fecprbact FROM tabla1 LIMIT 1').fetchone()
    if not hato or not hato['fecprbact']:
        conn.close()
        return jsonify({'success': False, 'error': 'Falta Fecha de Validacion'}), 400

    conn.execute(f'UPDATE tabla2 SET {campo}=? WHERE id=?', (valor_float, animal_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True})


@bp.route('/principal/api/novilla/<int:idx>')
def api_get_novilla(idx):
    """API para obtener datos de novilla via AJAX."""
    session_id = _get_session_id()
    if not session_id:
        return jsonify({'success': False, 'error': 'Sin sesión activa'}), 401

    conn = get_db(session_id)

    # Novillas con estado='0' de ambas tablas
    animales = conn.execute('''
        SELECT id, codint, orejera, nombre, 'tabla2' as tabla FROM tabla2 WHERE estado = '0'
        UNION ALL
        SELECT id, codint, orejera, nombre, 'tabla3' as tabla FROM tabla3 WHERE estado = '0'
        ORDER BY nombre
    ''').fetchall()

    if not animales:
        conn.close()
        return jsonify({'success': False, 'error': 'No hay novillas'}), 404

    # Validate index
    if idx < 0:
        idx = 0
    if idx >= len(animales):
        idx = len(animales) - 1

    animal_id = animales[idx]['id']
    tabla_origen = animales[idx]['tabla']

    # Obtener datos completos
    if tabla_origen == 'tabla2':
        animal_row = conn.execute('SELECT * FROM tabla2 WHERE id = ?', (animal_id,)).fetchone()
        animal = dict(animal_row)
    else:
        animal_t3 = conn.execute('SELECT * FROM tabla3 WHERE id = ?', (animal_id,)).fetchone()
        animal_t2 = conn.execute('SELECT fecser, toro, calor, fecparto, tipoparto, orecria1, nomcria1, sexcria1, hacer1, orecria2, nomcria2, sexcria2, hacer2, numser, fecultser FROM tabla2 WHERE codint = ?', (animal_t3['codint'],)).fetchone()
        animal = dict(animal_t3)
        if animal_t2:
            for key in ['fecser', 'toro', 'calor', 'fecparto', 'tipoparto', 'orecria1', 'nomcria1', 'sexcria1', 'hacer1', 'orecria2', 'nomcria2', 'sexcria2', 'hacer2', 'numser', 'fecultser']:
                animal[key] = animal_t2[key]

    conn.close()

    # Format dates
    def format_fecha(fecha_str):
        if not fecha_str:
            return '—'
        try:
            meses = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC']
            d = datetime.strptime(fecha_str, '%Y-%m-%d')
            return f"{d.day:02d}/{meses[d.month-1]}/{d.year}"
        except:
            return fecha_str or '—'

    # PAC mapping
    pac_val = str(animal.get('pac', '')).upper().strip()
    pac_map = {'A': 'Abierta', 'P': 'Preñada'}
    pac_color = {'A': 'danger', 'P': 'success'}

    return jsonify({
        'success': True,
        'animal_idx': idx,
        'total_animales': len(animales),
        'tabla_origen': tabla_origen,
        'animal': {
            'id': animal['id'],
            'orejera': animal.get('orejera', ''),
            'nombre': animal.get('nombre', ''),
            'codint': animal.get('codint', ''),
            'registro': animal.get('registro') or '—',
            'fecest': format_fecha(animal.get('fecest')),
            'fecest_raw': animal.get('fecest') or '',
            'diagnostico': pac_map.get(pac_val, '') if pac_val else '',
            'diagnostico_color': pac_color.get(pac_val, 'secondary'),
            'numser': animal.get('numser') or '0',
            'fecultser': format_fecha(animal.get('fecultser')),
            'fecultser_raw': animal.get('fecultser') or '',
            'toro': animal.get('codtor') or animal.get('toro') or '—',
            # Raw values for forms
            'fecser_raw': animal.get('fecser') or '',
            'toro_raw': animal.get('toro') or '',
            'calor': animal.get('calor') or '',
            'fecparto_raw': animal.get('fecparto') or '',
            'tipoparto': animal.get('tipoparto') or '',
            'hacer1': animal.get('hacer1') or '',
            'orecria1': animal.get('orecria1') or '',
            'nomcria1': animal.get('nomcria1') or '',
            'sexcria1': animal.get('sexcria1') or '',
            'hacer2': animal.get('hacer2') or '',
            'orecria2': animal.get('orecria2') or '',
            'nomcria2': animal.get('nomcria2') or '',
            'sexcria2': animal.get('sexcria2') or '',
        }
    })


@bp.route('/principal/novillas')
def novillas():
    """Vista para manejo de novillas (estado=0) de tabla2 y tabla3."""
    session_id = _get_session_id()
    if not session_id:
        return redirect(url_for('main.index'))

    conn = get_db(session_id)
    hato = conn.execute('SELECT * FROM tabla1 LIMIT 1').fetchone()

    # Validar que exista fecha de validacion
    if not hato or not hato['fecprbact']:
        conn.close()
        flash('Debe ingresar la Fecha de Validacion antes de acceder a Novillas.', 'warning')
        return redirect(url_for('principal.index'))

    # Novillas con estado='0' de ambas tablas
    animales = conn.execute('''
        SELECT id, codint, orejera, nombre, 'tabla2' as tabla FROM tabla2 WHERE estado = '0'
        UNION ALL
        SELECT id, codint, orejera, nombre, 'tabla3' as tabla FROM tabla3 WHERE estado = '0'
        ORDER BY nombre
    ''').fetchall()

    # Current animal index
    animal_idx = request.args.get('idx', 0, type=int)
    animal = None
    tabla_origen = None
    if animales:
        if animal_idx < 0:
            animal_idx = 0
        if animal_idx >= len(animales):
            animal_idx = len(animales) - 1
        animal_id = animales[animal_idx]['id']
        tabla_origen = animales[animal_idx]['tabla']

        # Obtener datos completos del animal desde su tabla de origen
        if tabla_origen == 'tabla2':
            animal = conn.execute('SELECT * FROM tabla2 WHERE id = ?', (animal_id,)).fetchone()
        else:
            # Obtener datos basicos de tabla3
            animal_t3 = conn.execute('SELECT * FROM tabla3 WHERE id = ?', (animal_id,)).fetchone()
            # Buscar datos de servicio/parto en tabla2 (si existen)
            animal_t2 = conn.execute('SELECT fecser, toro, calor, fecparto, tipoparto, orecria1, nomcria1, sexcria1, hacer1, orecria2, nomcria2, sexcria2, hacer2 FROM tabla2 WHERE codint = ?', (animal_t3['codint'],)).fetchone()

            # Combinar datos: usar tabla3 como base y sobrescribir con datos de tabla2 si existen
            animal_dict = dict(animal_t3)
            if animal_t2:
                # Sobrescribir campos de servicio/parto con los de tabla2
                animal_dict['fecser'] = animal_t2['fecser']
                animal_dict['toro'] = animal_t2['toro']
                animal_dict['calor'] = animal_t2['calor']
                animal_dict['fecparto'] = animal_t2['fecparto']
                animal_dict['tipoparto'] = animal_t2['tipoparto']
                animal_dict['orecria1'] = animal_t2['orecria1']
                animal_dict['nomcria1'] = animal_t2['nomcria1']
                animal_dict['sexcria1'] = animal_t2['sexcria1']
                animal_dict['hacer1'] = animal_t2['hacer1']
                animal_dict['orecria2'] = animal_t2['orecria2']
                animal_dict['nomcria2'] = animal_t2['nomcria2']
                animal_dict['sexcria2'] = animal_t2['sexcria2']
                animal_dict['hacer2'] = animal_t2['hacer2']
            animal = animal_dict

    # Active tab
    tab = request.args.get('tab', 'servicios')

    conn.close()

    # Date limits for novelty fields
    fecha_min = hato['fecultprb'] or '' if hato else ''
    fecha_max = hato['fecprbact'] or '' if hato else ''

    # Calcular fecha minima para servicios (125 dias antes de fecha de validacion)
    fecha_min_servicio = ''
    if fecha_max:
        try:
            fec_val = datetime.strptime(fecha_max, '%Y-%m-%d')
            fec_min_ser = fec_val - timedelta(days=125)
            fecha_min_servicio = fec_min_ser.strftime('%Y-%m-%d')
        except ValueError:
            fecha_min_servicio = fecha_min

    return render_template('novillas.html',
                           hato=hato,
                           animales=animales,
                           animal=animal,
                           animal_idx=animal_idx,
                           total_animales=len(animales),
                           tab=tab,
                           fecha_min=fecha_min,
                           fecha_max=fecha_max,
                           fecha_min_servicio=fecha_min_servicio,
                           tabla_origen=tabla_origen)


@bp.route('/principal/novillas/servicio/<int:animal_id>', methods=['POST'])
def novillas_servicio(animal_id):
    """Guardar servicio para una novilla. Siempre se guarda en tabla2."""
    session_id = _get_session_id()
    if not session_id:
        return redirect(url_for('main.index'))

    conn = get_db(session_id)

    # Validar que exista fecha de validacion
    hato = conn.execute('SELECT fecprbact FROM tabla1 LIMIT 1').fetchone()
    if not hato or not hato['fecprbact']:
        conn.close()
        flash('Debe ingresar la Fecha de Validacion antes de registrar novedades.', 'warning')
        return redirect(url_for('principal.index'))

    idx = request.form.get('idx', 0, type=int)
    tabla_origen = request.form.get('tabla', 'tabla2')

    # Obtener el animal desde su tabla de origen
    if tabla_origen == 'tabla2':
        animal = conn.execute('SELECT * FROM tabla2 WHERE id = ?', (animal_id,)).fetchone()
    else:
        animal = conn.execute('SELECT * FROM tabla3 WHERE id = ?', (animal_id,)).fetchone()

    if not animal:
        conn.close()
        flash('Animal no encontrado.', 'danger')
        return redirect(url_for('principal.novillas'))

    # Verificar que fecest sea mayor a 1 año
    if animal['fecest']:
        try:
            fecest = datetime.strptime(animal['fecest'], '%Y-%m-%d')
            hoy = datetime.now()
            dias = (hoy - fecest).days
            if dias < 365:
                conn.close()
                flash(f'No se puede registrar servicio. La novilla debe tener al menos 1 año de edad. Dias desde fecha estado: {dias}', 'danger')
                return redirect(url_for('principal.novillas', idx=idx, tab='servicios'))
        except ValueError:
            pass

    fecser = request.form.get('fecser', '').strip() or None
    toro = request.form.get('toro', '').strip().upper() or None
    calor = request.form.get('calor', '').strip() or None

    # Si calor perdido, poner CALOR PER en el campo toro
    if calor == 'S':
        toro = 'CALOR PER'

    # Siempre guardar en tabla2
    if tabla_origen == 'tabla2':
        # Animal ya esta en tabla2, solo actualizar
        conn.execute('''
            UPDATE tabla2
            SET fecser = ?, toro = ?, calor = ?
            WHERE id = ?
        ''', (fecser, toro, calor, animal_id))
    else:
        # Animal viene de tabla3, buscar por codint en tabla2 o actualizar por codint
        animal_t2 = conn.execute('SELECT id FROM tabla2 WHERE codint = ?', (animal['codint'],)).fetchone()
        if animal_t2:
            # Existe en tabla2, actualizar
            conn.execute('''
                UPDATE tabla2
                SET fecser = ?, toro = ?, calor = ?
                WHERE codint = ?
            ''', (fecser, toro, calor, animal['codint']))
        else:
            # No existe en tabla2, insertar nuevo registro con todos los campos
            conn.execute('''
                INSERT INTO tabla2 (codint, orejera, nombre, registro, estado, fecest,
                    ultlec, dialec, numser, fecultser, pac, numreb,
                    fecser, toro, calor, nuevo, codtor, clasi, ptos,
                    ord1, ord2, ord3)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                animal['codint'],
                animal['orejera'],
                animal['nombre'],
                animal['registro'],  # Copiar registro de tabla3
                animal['estado'],
                animal['fecest'],
                animal['ultlec'] if animal['ultlec'] is not None else 0.0,  # ultlec = 0.0 si es NULL
                animal['dialec'] if animal['dialec'] is not None else 0,    # dialec = 0 si es NULL
                animal['numser'] if animal['numser'] is not None else 0,    # numser = 0 si es NULL
                animal['fecultser'],
                animal['pac'],
                animal['numreb'] if animal['numreb'] is not None else 0,    # numreb = 0 si es NULL
                fecser,
                toro,
                calor,
                1,  # nuevo = 1 (.T. en VFP) para indicar que viene de tabla3
                animal['codtor'],
                animal['clasi'],
                animal['ptos'],
                0.0,  # ord1 = 0.0
                0.0,  # ord2 = 0.0
                0.0   # ord3 = 0.0
            ))

    conn.commit()
    conn.close()

    flash('Servicio guardado.', 'success')
    return redirect(url_for('principal.novillas', idx=idx, tab='servicios'))


@bp.route('/principal/novillas/parto/<int:animal_id>', methods=['POST'])
def novillas_parto(animal_id):
    """Guardar parto para una novilla. Siempre se guarda en tabla2."""
    session_id = _get_session_id()
    if not session_id:
        return redirect(url_for('main.index'))

    conn = get_db(session_id)

    # Validar que exista fecha de validacion
    hato = conn.execute('SELECT fecprbact FROM tabla1 LIMIT 1').fetchone()
    if not hato or not hato['fecprbact']:
        conn.close()
        flash('Debe ingresar la Fecha de Validacion antes de registrar novedades.', 'warning')
        return redirect(url_for('principal.index'))

    idx = request.form.get('idx', 0, type=int)
    tabla_origen = request.form.get('tabla', 'tabla2')

    # Obtener el animal desde su tabla de origen
    if tabla_origen == 'tabla2':
        animal = conn.execute('SELECT * FROM tabla2 WHERE id = ?', (animal_id,)).fetchone()
    else:
        animal = conn.execute('SELECT * FROM tabla3 WHERE id = ?', (animal_id,)).fetchone()

    if not animal:
        conn.close()
        flash('Animal no encontrado.', 'danger')
        return redirect(url_for('principal.novillas'))

    # Verificar que tiene servicio (buscar en tabla2 si viene de tabla3)
    tiene_servicio = animal['fecser']
    if tabla_origen == 'tabla3' and not tiene_servicio:
        # Verificar si existe en tabla2 con servicio
        animal_t2 = conn.execute('SELECT fecser FROM tabla2 WHERE codint = ?', (animal['codint'],)).fetchone()
        if animal_t2:
            tiene_servicio = animal_t2['fecser']

    if not tiene_servicio:
        conn.close()
        flash('No se puede registrar parto. La novilla debe tener al menos un servicio reportado.', 'danger')
        return redirect(url_for('principal.novillas', idx=idx, tab='partos'))

    fecparto = request.form.get('fecparto', '').strip() or None
    tipoparto = request.form.get('tipoparto', '').strip() or None
    orecria1 = request.form.get('orecria1', '').strip() or None
    nomcria1 = request.form.get('nomcria1', '').strip() or None
    sexcria1 = request.form.get('sexcria1', '').strip() or None
    hacer1 = request.form.get('hacer1', '').strip() or None
    orecria2 = request.form.get('orecria2', '').strip() or None
    nomcria2 = request.form.get('nomcria2', '').strip() or None
    sexcria2 = request.form.get('sexcria2', '').strip() or None
    hacer2 = request.form.get('hacer2', '').strip() or None

    # Siempre guardar en tabla2
    if tabla_origen == 'tabla2':
        conn.execute('''
            UPDATE tabla2 SET fecparto=?, tipoparto=?,
               orecria1=?, nomcria1=?, sexcria1=?, hacer1=?,
               orecria2=?, nomcria2=?, sexcria2=?, hacer2=?
               WHERE id=?
        ''', (fecparto, tipoparto, orecria1, nomcria1, sexcria1, hacer1,
              orecria2, nomcria2, sexcria2, hacer2, animal_id))
    else:
        # Animal viene de tabla3, actualizar por codint en tabla2
        animal_t2 = conn.execute('SELECT id FROM tabla2 WHERE codint = ?', (animal['codint'],)).fetchone()
        if animal_t2:
            conn.execute('''
                UPDATE tabla2 SET fecparto=?, tipoparto=?,
                   orecria1=?, nomcria1=?, sexcria1=?, hacer1=?,
                   orecria2=?, nomcria2=?, sexcria2=?, hacer2=?
                   WHERE codint=?
            ''', (fecparto, tipoparto, orecria1, nomcria1, sexcria1, hacer1,
                  orecria2, nomcria2, sexcria2, hacer2, animal['codint']))
        else:
            conn.close()
            flash('Error: El animal debe tener un servicio registrado primero.', 'danger')
            return redirect(url_for('principal.novillas', idx=idx, tab='partos'))

    conn.commit()
    conn.close()

    flash('Parto guardado.', 'success')
    return redirect(url_for('principal.novillas', idx=idx, tab='partos'))


@bp.route('/principal/novillas/borrar/servicio/<int:animal_id>', methods=['POST'])
def novillas_borrar_servicio(animal_id):
    """Borrar servicio de una novilla. Siempre se borra de tabla2."""
    session_id = _get_session_id()
    if not session_id:
        return redirect(url_for('main.index'))
    conn = get_db(session_id)
    idx = request.form.get('idx', 0, type=int)
    tabla_origen = request.form.get('tabla', 'tabla2')

    if tabla_origen == 'tabla2':
        conn.execute('UPDATE tabla2 SET fecser=NULL, toro=NULL, calor=NULL WHERE id=?', (animal_id,))
    else:
        # Animal viene de tabla3, borrar de tabla2 por codint
        animal = conn.execute('SELECT codint FROM tabla3 WHERE id = ?', (animal_id,)).fetchone()
        if animal:
            conn.execute('UPDATE tabla2 SET fecser=NULL, toro=NULL, calor=NULL WHERE codint=?', (animal['codint'],))

    conn.commit()
    conn.close()
    flash('Servicio eliminado.', 'success')
    return redirect(url_for('principal.novillas', idx=idx, tab='servicios'))


@bp.route('/principal/novillas/borrar/parto/<int:animal_id>', methods=['POST'])
def novillas_borrar_parto(animal_id):
    """Borrar parto de una novilla. Siempre se borra de tabla2."""
    session_id = _get_session_id()
    if not session_id:
        return redirect(url_for('main.index'))
    conn = get_db(session_id)
    idx = request.form.get('idx', 0, type=int)
    tabla_origen = request.form.get('tabla', 'tabla2')

    if tabla_origen == 'tabla2':
        conn.execute('''UPDATE tabla2 SET fecparto=NULL, tipoparto=NULL,
                        orecria1=NULL, nomcria1=NULL, sexcria1=NULL, hacer1=NULL,
                        orecria2=NULL, nomcria2=NULL, sexcria2=NULL, hacer2=NULL
                        WHERE id=?''', (animal_id,))
    else:
        # Animal viene de tabla3, borrar de tabla2 por codint
        animal = conn.execute('SELECT codint FROM tabla3 WHERE id = ?', (animal_id,)).fetchone()
        if animal:
            conn.execute('''UPDATE tabla2 SET fecparto=NULL, tipoparto=NULL,
                            orecria1=NULL, nomcria1=NULL, sexcria1=NULL, hacer1=NULL,
                            orecria2=NULL, nomcria2=NULL, sexcria2=NULL, hacer2=NULL
                            WHERE codint=?''', (animal['codint'],))

    conn.commit()
    conn.close()
    flash('Parto eliminado.', 'success')
    return redirect(url_for('principal.novillas', idx=idx, tab='partos'))


@bp.route('/principal/resumen')
def resumen_general():
    """Resumen general de todas las novedades digitadas."""
    session_id = _get_session_id()
    if not session_id:
        return redirect(url_for('main.index'))

    conn = get_db(session_id)
    hato = conn.execute('SELECT * FROM tabla1 LIMIT 1').fetchone()

    # Servicios registrados (fecser no nulo)
    servicios = conn.execute('''
        SELECT id, orejera, nombre, fecser, toro, calor
        FROM tabla2
        WHERE fecser IS NOT NULL
        ORDER BY nombre
    ''').fetchall()

    # Secas registradas (fecseca no nulo)
    secas = conn.execute('''
        SELECT id, orejera, nombre, fecseca
        FROM tabla2
        WHERE fecseca IS NOT NULL
        ORDER BY nombre
    ''').fetchall()

    # Chequeos de preñez registrados (fecchp no nulo)
    chequeos = conn.execute('''
        SELECT id, orejera, nombre, fecchp, panew
        FROM tabla2
        WHERE fecchp IS NOT NULL
        ORDER BY nombre
    ''').fetchall()

    # Partos registrados (fecparto no nulo)
    partos = conn.execute('''
        SELECT id, orejera, nombre, fecparto, tipoparto,
               orecria1, nomcria1, sexcria1, hacer1,
               orecria2, nomcria2, sexcria2, hacer2
        FROM tabla2
        WHERE fecparto IS NOT NULL
        ORDER BY nombre
    ''').fetchall()

    # Salidas registradas (fecsale no nulo)
    salidas = conn.execute('''
        SELECT id, orejera, nombre, fecsale, motsale
        FROM tabla2
        WHERE fecsale IS NOT NULL
        ORDER BY nombre
    ''').fetchall()

    # Ordeños registrados (ord1, ord2 o ord3 mayor a 0)
    ordenos = conn.execute('''
        SELECT id, orejera, nombre, ord1, ord2, ord3
        FROM tabla2
        WHERE (ord1 IS NOT NULL AND ord1 > 0)
           OR (ord2 IS NOT NULL AND ord2 > 0)
           OR (ord3 IS NOT NULL AND ord3 > 0)
        ORDER BY nombre
    ''').fetchall()

    # Registros sanitarios (solo valores digitados por el usuario: S, M, U, T, L)
    sanitarios = conn.execute('''
        SELECT id, orejera, nombre, cart
        FROM tabla2
        WHERE cart IN ('S', 'M', 'U', 'T', 'L')
        ORDER BY nombre
    ''').fetchall()

    conn.close()

    return render_template('resumen_general.html',
                           hato=hato,
                           servicios=servicios,
                           secas=secas,
                           chequeos=chequeos,
                           partos=partos,
                           salidas=salidas,
                           ordenos=ordenos,
                           sanitarios=sanitarios)


@bp.route('/principal/hato', methods=['POST'])
def update_hato():
    """Update farm validation date, milk total, and elaborated by."""
    from datetime import datetime, timedelta

    session_id = _get_session_id()
    if not session_id:
        return redirect(url_for('main.index'))

    conn = get_db(session_id)

    fecprbact = request.form.get('fecprbact', '').strip()
    sumlec = request.form.get('sumlec', '').strip()
    elaboraa = request.form.get('elaboraa', '').strip()

    if not fecprbact:
        flash('La fecha de validacion es obligatoria.', 'danger')
        conn.close()
        return redirect(url_for('principal.index'))

    # Obtener fecha de ultima prueba para validaciones
    hato = conn.execute('SELECT fecultprb FROM tabla1 WHERE id = 1').fetchone()
    fecultprb = hato['fecultprb'] if hato else None

    try:
        fecha_validacion = datetime.strptime(fecprbact, '%Y-%m-%d').date()
        hoy = datetime.now().date()

        # Validacion 1: No puede ser mayor a hoy
        if fecha_validacion > hoy:
            flash('La fecha de validacion no puede ser mayor a la fecha de hoy.', 'danger')
            conn.close()
            return redirect(url_for('principal.index'))

        # Validaciones que dependen de fecultprb
        if fecultprb:
            fecha_ult_prueba = datetime.strptime(fecultprb, '%Y-%m-%d').date()

            # Validacion 2: No puede ser inferior a la fecha de la ultima prueba
            if fecha_validacion < fecha_ult_prueba:
                flash('La fecha de validacion no puede ser anterior a la ultima prueba.', 'danger')
                conn.close()
                return redirect(url_for('principal.index'))

            # Validacion 3: No puede ser mayor a 45 dias despues de la ultima prueba
            fecha_limite = fecha_ult_prueba + timedelta(days=45)
            if fecha_validacion > fecha_limite:
                flash('La fecha de validacion no puede ser mayor a 45 dias despues de la ultima prueba.', 'danger')
                conn.close()
                return redirect(url_for('principal.index'))

    except ValueError:
        flash('Formato de fecha invalido.', 'danger')
        conn.close()
        return redirect(url_for('principal.index'))

    sumlec_val = float(sumlec) if sumlec else None

    conn.execute(
        'UPDATE tabla1 SET fecprbact = ?, sumlec = ?, elaboraa = ? WHERE id = 1',
        (fecprbact, sumlec_val, elaboraa)
    )
    conn.commit()
    conn.close()

    flash('Informacion del hato actualizada.', 'success')
    return redirect(url_for('principal.index'))


@bp.route('/principal/animal/<int:animal_id>/servicios', methods=['POST'])
def update_servicios(animal_id):
    """Update service info for an animal."""
    session_id = _get_session_id()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not session_id:
        if is_ajax:
            return jsonify({'success': False, 'message': 'Sesion no activa'}), 401
        return redirect(url_for('main.index'))

    conn = get_db(session_id)
    idx = request.form.get('idx', 0, type=int)

    fecser = request.form.get('fecser', '').strip() or None
    toro_input = request.form.get('toro', '').strip().upper() or None
    calor = request.form.get('calor', '').strip() or None

    # Si calor perdido, poner CALOR PER en el campo toro
    if calor == 'S':
        toro_input = 'CALOR PER'

    conn.execute(
        'UPDATE tabla2 SET fecser = ?, toro = ?, calor = ? WHERE id = ?',
        (fecser, toro_input, calor, animal_id)
    )
    conn.commit()
    conn.close()

    if is_ajax:
        return jsonify({'success': True, 'message': 'Servicio guardado'})

    flash('Servicio guardado.', 'success')
    return redirect(url_for('principal.index', idx=idx, tab='servicios'))


@bp.route('/principal/animal/<int:animal_id>/secas', methods=['POST'])
def update_secas(animal_id):
    session_id = _get_session_id()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not session_id:
        if is_ajax:
            return jsonify({'success': False, 'message': 'Sesion no activa'}), 401
        return redirect(url_for('main.index'))

    conn = get_db(session_id)
    idx = request.form.get('idx', 0, type=int)

    # Validar estado: solo 1 (vaca parida) o 2 (novilla parida)
    animal = conn.execute('SELECT estado FROM tabla2 WHERE id = ?', (animal_id,)).fetchone()
    if animal and animal['estado'] not in ('1', '2'):
        conn.close()
        msg = 'Solo se puede secar un animal en estado 1 (Vaca parida) o 2 (Novilla parida).'
        if is_ajax:
            return jsonify({'success': False, 'message': msg}), 400
        flash(msg, 'danger')
        return redirect(url_for('principal.index', idx=idx, tab='secas'))

    fecseca = request.form.get('fecseca', '').strip() or None

    conn.execute('UPDATE tabla2 SET fecseca = ? WHERE id = ?', (fecseca, animal_id))
    conn.commit()
    conn.close()

    if is_ajax:
        return jsonify({'success': True, 'message': 'Seca guardada'})

    flash('Seca guardada.', 'success')
    return redirect(url_for('principal.index', idx=idx, tab='secas'))


@bp.route('/principal/animal/<int:animal_id>/chequeo', methods=['POST'])
def update_chequeo(animal_id):
    session_id = _get_session_id()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not session_id:
        if is_ajax:
            return jsonify({'success': False, 'message': 'Sesion no activa'}), 401
        return redirect(url_for('main.index'))

    conn = get_db(session_id)
    idx = request.form.get('idx', 0, type=int)

    # Validar que tenga al menos un servicio
    animal = conn.execute('SELECT numser FROM tabla2 WHERE id = ?', (animal_id,)).fetchone()
    if not animal or not animal['numser'] or animal['numser'] <= 0:
        conn.close()
        msg = 'Solo se puede chequear preñez de un animal con al menos un servicio registrado.'
        if is_ajax:
            return jsonify({'success': False, 'message': msg}), 400
        flash(msg, 'danger')
        return redirect(url_for('principal.index', idx=idx, tab='chequeo'))

    fecchp = request.form.get('fecchp', '').strip() or None
    panew = request.form.get('panew', '').strip().upper() or None

    conn.execute('UPDATE tabla2 SET fecchp = ?, panew = ? WHERE id = ?', (fecchp, panew, animal_id))
    conn.commit()
    conn.close()

    if is_ajax:
        return jsonify({'success': True, 'message': 'Chequeo guardado'})

    flash('Chequeo de preñez guardado.', 'success')
    return redirect(url_for('principal.index', idx=idx, tab='chequeo'))


@bp.route('/principal/animal/<int:animal_id>/partos', methods=['POST'])
def update_partos(animal_id):
    session_id = _get_session_id()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not session_id:
        if is_ajax:
            return jsonify({'success': False, 'message': 'Sesion no activa'}), 401
        return redirect(url_for('main.index'))

    conn = get_db(session_id)
    idx = request.form.get('idx', 0, type=int)

    # Validar estado: 0 (Ternera), 6 (Seca) o que tenga fecha de seca
    # Si viene forzar_aborto=1, se permite desde cualquier estado (solo aborto)
    forzar_aborto = request.form.get('forzar_aborto', '0') == '1'
    animal_check = conn.execute('SELECT estado, fecseca, fecultser FROM tabla2 WHERE id = ?', (animal_id,)).fetchone()
    if animal_check and not forzar_aborto:
        puede_parir = animal_check['estado'] in ('0', '6') or animal_check['fecseca']
        if not puede_parir:
            conn.close()
            msg = 'Solo se puede registrar un parto para un animal en estado 0 (Ternera), 6 (Seca) o con fecha de seca registrada.'
            if is_ajax:
                return jsonify({'success': False, 'message': msg}), 400
            flash(msg, 'danger')
            return redirect(url_for('principal.index', idx=idx, tab='partos'))

    fecparto = request.form.get('fecparto', '').strip() or None

    # Validar 152 dias entre fecha ultimo servicio y fecha de parto para abortos forzados
    if forzar_aborto and fecparto and animal_check and animal_check['fecultser']:
        try:
            d_servicio = datetime.strptime(animal_check['fecultser'], '%Y-%m-%d')
            d_parto = datetime.strptime(fecparto, '%Y-%m-%d')
            dias = (d_parto - d_servicio).days
            if dias < 152:
                conn.close()
                msg = f'No se puede registrar el aborto. Deben transcurrir al menos 152 dias desde la Fec. Ult. Serv. Dias transcurridos: {dias}.'
                if is_ajax:
                    return jsonify({'success': False, 'message': msg}), 400
                flash(msg, 'danger')
                return redirect(url_for('principal.index', idx=idx, tab='partos'))
        except ValueError:
            pass
    tipoparto = request.form.get('tipoparto', '').strip() or None
    orecria1 = request.form.get('orecria1', '').strip() or None
    nomcria1 = request.form.get('nomcria1', '').strip() or None
    sexcria1 = request.form.get('sexcria1', '').strip() or None
    hacer1 = request.form.get('hacer1', '').strip() or None
    orecria2 = request.form.get('orecria2', '').strip() or None
    nomcria2 = request.form.get('nomcria2', '').strip() or None
    sexcria2 = request.form.get('sexcria2', '').strip() or None
    hacer2 = request.form.get('hacer2', '').strip() or None

    conn.execute(
        '''UPDATE tabla2 SET fecparto=?, tipoparto=?,
           orecria1=?, nomcria1=?, sexcria1=?, hacer1=?,
           orecria2=?, nomcria2=?, sexcria2=?, hacer2=?
           WHERE id=?''',
        (fecparto, tipoparto, orecria1, nomcria1, sexcria1, hacer1,
         orecria2, nomcria2, sexcria2, hacer2, animal_id)
    )
    conn.commit()
    conn.close()

    if is_ajax:
        return jsonify({'success': True, 'message': 'Parto guardado'})

    flash('Parto guardado.', 'success')
    return redirect(url_for('principal.index', idx=idx, tab='partos'))


@bp.route('/principal/animal/<int:animal_id>/salidas', methods=['POST'])
def update_salidas(animal_id):
    session_id = _get_session_id()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not session_id:
        if is_ajax:
            return jsonify({'success': False, 'message': 'Sesion no activa'}), 401
        return redirect(url_for('main.index'))

    conn = get_db(session_id)
    idx = request.form.get('idx', 0, type=int)

    fecsale = request.form.get('fecsale', '').strip() or None
    motsale = request.form.get('motsale', '').strip() or None

    conn.execute('UPDATE tabla2 SET fecsale=?, motsale=? WHERE id=?',
                 (fecsale, motsale, animal_id))
    conn.commit()
    conn.close()

    if is_ajax:
        return jsonify({'success': True, 'message': 'Salida guardada'})

    flash('Salida guardada.', 'success')
    return redirect(url_for('principal.index', idx=idx, tab='salidas'))


@bp.route('/principal/animal/<int:animal_id>/ordenos', methods=['POST'])
def update_ordenos(animal_id):
    session_id = _get_session_id()
    if not session_id:
        return redirect(url_for('main.index'))

    conn = get_db(session_id)
    idx = request.form.get('idx', 0, type=int)

    ord1 = request.form.get('ord1', '').strip()
    ord2 = request.form.get('ord2', '').strip()
    ord3 = request.form.get('ord3', '').strip()

    ord1 = float(ord1) if ord1 else None
    ord2 = float(ord2) if ord2 else None
    ord3 = float(ord3) if ord3 else None

    conn.execute('UPDATE tabla2 SET ord1=?, ord2=?, ord3=? WHERE id=?',
                 (ord1, ord2, ord3, animal_id))
    conn.commit()
    conn.close()

    flash('Ordeños guardados.', 'success')
    return redirect(url_for('principal.index', idx=idx, tab='ordenos'))


@bp.route('/principal/animal/<int:animal_id>/sanitario', methods=['POST'])
def update_sanitario(animal_id):
    """Update sanitary info for an animal."""
    session_id = _get_session_id()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not session_id:
        if is_ajax:
            return jsonify({'success': False, 'message': 'Sesion no activa'}), 401
        return redirect(url_for('main.index'))

    conn = get_db(session_id)
    idx = request.form.get('idx', 0, type=int)

    cart = request.form.get('cart', '').strip() or None

    conn.execute('UPDATE tabla2 SET cart=? WHERE id=?', (cart, animal_id))
    conn.commit()
    conn.close()

    if is_ajax:
        return jsonify({'success': True, 'message': 'Sanitario guardado'})

    flash('Registro sanitario guardado.', 'success')
    return redirect(url_for('principal.index', idx=idx, tab='sanitario'))


# ---- RUTAS PARA BORRAR DATOS ----

@bp.route('/principal/animal/<int:animal_id>/borrar/servicios', methods=['POST'])
def borrar_servicios(animal_id):
    session_id = _get_session_id()
    if not session_id:
        return redirect(url_for('main.index'))
    conn = get_db(session_id)
    idx = request.form.get('idx', 0, type=int)
    conn.execute('UPDATE tabla2 SET fecser=NULL, toro=NULL, calor=NULL WHERE id=?', (animal_id,))
    conn.commit()
    conn.close()
    flash('Servicio eliminado.', 'success')
    return redirect(url_for('principal.index', idx=idx, tab='servicios'))


@bp.route('/principal/animal/<int:animal_id>/borrar/secas', methods=['POST'])
def borrar_secas(animal_id):
    session_id = _get_session_id()
    if not session_id:
        return redirect(url_for('main.index'))
    conn = get_db(session_id)
    idx = request.form.get('idx', 0, type=int)
    conn.execute('UPDATE tabla2 SET fecseca=NULL WHERE id=?', (animal_id,))
    conn.commit()
    conn.close()
    flash('Seca eliminada.', 'success')
    return redirect(url_for('principal.index', idx=idx, tab='secas'))


@bp.route('/principal/animal/<int:animal_id>/borrar/chequeo', methods=['POST'])
def borrar_chequeo(animal_id):
    session_id = _get_session_id()
    if not session_id:
        return redirect(url_for('main.index'))
    conn = get_db(session_id)
    idx = request.form.get('idx', 0, type=int)
    conn.execute('UPDATE tabla2 SET fecchp=NULL, panew=NULL WHERE id=?', (animal_id,))
    conn.commit()
    conn.close()
    flash('Chequeo eliminado.', 'success')
    return redirect(url_for('principal.index', idx=idx, tab='chequeo'))


@bp.route('/principal/animal/<int:animal_id>/borrar/partos', methods=['POST'])
def borrar_partos(animal_id):
    session_id = _get_session_id()
    if not session_id:
        return redirect(url_for('main.index'))
    conn = get_db(session_id)
    idx = request.form.get('idx', 0, type=int)
    conn.execute('''UPDATE tabla2 SET fecparto=NULL, tipoparto=NULL,
                    orecria1=NULL, nomcria1=NULL, sexcria1=NULL, hacer1=NULL,
                    orecria2=NULL, nomcria2=NULL, sexcria2=NULL, hacer2=NULL
                    WHERE id=?''', (animal_id,))
    conn.commit()
    conn.close()
    flash('Parto eliminado.', 'success')
    return redirect(url_for('principal.index', idx=idx, tab='partos'))


@bp.route('/principal/animal/<int:animal_id>/borrar/salidas', methods=['POST'])
def borrar_salidas(animal_id):
    session_id = _get_session_id()
    if not session_id:
        return redirect(url_for('main.index'))
    conn = get_db(session_id)
    idx = request.form.get('idx', 0, type=int)
    conn.execute('UPDATE tabla2 SET fecsale=NULL, motsale=NULL WHERE id=?', (animal_id,))
    conn.commit()
    conn.close()
    flash('Salida eliminada.', 'success')
    return redirect(url_for('principal.index', idx=idx, tab='salidas'))


@bp.route('/principal/animal/<int:animal_id>/borrar/ordenos', methods=['POST'])
def borrar_ordenos(animal_id):
    session_id = _get_session_id()
    if not session_id:
        return redirect(url_for('main.index'))
    conn = get_db(session_id)
    idx = request.form.get('idx', 0, type=int)
    conn.execute('UPDATE tabla2 SET ord1=NULL, ord2=NULL, ord3=NULL WHERE id=?', (animal_id,))
    conn.commit()
    conn.close()
    flash('Ordeños eliminados.', 'success')
    return redirect(url_for('principal.index', idx=idx, tab='ordenos'))


@bp.route('/principal/animal/<int:animal_id>/borrar/sanitario', methods=['POST'])
def borrar_sanitario(animal_id):
    session_id = _get_session_id()
    if not session_id:
        return redirect(url_for('main.index'))
    conn = get_db(session_id)
    idx = request.form.get('idx', 0, type=int)
    conn.execute('UPDATE tabla2 SET cart=NULL WHERE id=?', (animal_id,))
    conn.commit()
    conn.close()
    flash('Registro sanitario eliminado.', 'success')
    return redirect(url_for('principal.index', idx=idx, tab='sanitario'))


@bp.route('/principal/ver-tabla')
def ver_tabla():
    """Vista para ver los datos de tabla2 tal cual estan en la base de datos."""
    session_id = _get_session_id()
    if not session_id:
        return redirect(url_for('main.index'))

    conn = get_db(session_id)
    hato = conn.execute('SELECT * FROM tabla1 LIMIT 1').fetchone()

    # Obtener nombres de columnas de tabla2
    cursor = conn.execute('SELECT * FROM tabla2 LIMIT 1')
    columnas = [description[0] for description in cursor.description]

    # Obtener todos los registros
    registros = conn.execute('SELECT * FROM tabla2 ORDER BY id').fetchall()

    conn.close()

    return render_template('ver_tabla.html',
                           hato=hato,
                           columnas=columnas,
                           registros=registros)
