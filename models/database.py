import os
import sqlite3
import config

TABLA2_COLUMNS = """
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codint TEXT,
    orejera TEXT,
    nombre TEXT,
    registro TEXT,
    estado TEXT,
    fecest TEXT,
    ultlec REAL,
    dialec INTEGER,
    numser INTEGER,
    fecultser TEXT,
    pac TEXT,
    numreb INTEGER,
    fecser TEXT,
    toro TEXT,
    fecseca TEXT,
    fecchp TEXT,
    panew TEXT,
    fecparto TEXT,
    orecria1 TEXT,
    nomcria1 TEXT,
    sexcria1 TEXT,
    orecria2 TEXT,
    nomcria2 TEXT,
    sexcria2 TEXT,
    cart TEXT,
    fecsale TEXT,
    motsale TEXT,
    ord1 REAL,
    ord2 REAL,
    ord3 REAL,
    tipoparto TEXT,
    hacer1 TEXT,
    hacer2 TEXT,
    calor TEXT,
    nuevo INTEGER,
    codtor TEXT,
    clasi TEXT,
    ptos INTEGER
"""

SCHEMA_SQL = f"""
CREATE TABLE IF NOT EXISTS session_meta (
    id INTEGER PRIMARY KEY,
    prefix_code TEXT NOT NULL,
    farm_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active',
    device_id TEXT
);

CREATE TABLE IF NOT EXISTS tabla1 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hato TEXT,
    nombre TEXT,
    propieta TEXT,
    fecultprb TEXT,
    elaborau TEXT,
    fecprbact TEXT,
    elaboraa TEXT,
    sumlec REAL
);

CREATE TABLE IF NOT EXISTS tabla2 (
    {TABLA2_COLUMNS}
);

CREATE TABLE IF NOT EXISTS tabla3 (
    {TABLA2_COLUMNS}
);

-- Indices para mejorar rendimiento de consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_tabla2_estado ON tabla2(estado);
CREATE INDEX IF NOT EXISTS idx_tabla2_codint ON tabla2(codint);
CREATE INDEX IF NOT EXISTS idx_tabla2_nombre ON tabla2(nombre);
CREATE INDEX IF NOT EXISTS idx_tabla2_fecser ON tabla2(fecser);
CREATE INDEX IF NOT EXISTS idx_tabla2_fecseca ON tabla2(fecseca);
CREATE INDEX IF NOT EXISTS idx_tabla2_fecchp ON tabla2(fecchp);
CREATE INDEX IF NOT EXISTS idx_tabla2_fecparto ON tabla2(fecparto);
CREATE INDEX IF NOT EXISTS idx_tabla2_fecsale ON tabla2(fecsale);

CREATE INDEX IF NOT EXISTS idx_tabla3_estado ON tabla3(estado);
CREATE INDEX IF NOT EXISTS idx_tabla3_codint ON tabla3(codint);
CREATE INDEX IF NOT EXISTS idx_tabla3_nombre ON tabla3(nombre);
CREATE INDEX IF NOT EXISTS idx_tabla3_fecser ON tabla3(fecser);
CREATE INDEX IF NOT EXISTS idx_tabla3_fecparto ON tabla3(fecparto);
"""

# Field names matching the actual .dbf columns
ANIMAL_FIELDS = [
    'codint', 'orejera', 'nombre', 'registro', 'estado', 'fecest',
    'ultlec', 'dialec', 'numser', 'fecultser', 'pac', 'numreb',
    'fecser', 'toro', 'fecseca', 'fecchp', 'panew', 'fecparto',
    'orecria1', 'nomcria1', 'sexcria1',
    'orecria2', 'nomcria2', 'sexcria2',
    'cart', 'fecsale', 'motsale',
    'ord1', 'ord2', 'ord3',
    'tipoparto', 'hacer1', 'hacer2', 'calor',
    'nuevo', 'codtor', 'clasi', 'ptos'
]

TABLA1_FIELDS = [
    'hato', 'nombre', 'propieta', 'fecultprb',
    'elaborau', 'fecprbact', 'elaboraa', 'sumlec'
]


def get_db_path(session_id):
    return os.path.join(config.DATA_FOLDER, f'session_{session_id}.db')


def get_db(session_id):
    db_path = get_db_path(session_id)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Optimizaciones SQLite para mejor rendimiento
    conn.execute('PRAGMA journal_mode = WAL')
    conn.execute('PRAGMA synchronous = NORMAL')
    conn.execute('PRAGMA cache_size = 10000')
    conn.execute('PRAGMA temp_store = MEMORY')
    return conn


def init_db(session_id):
    conn = get_db(session_id)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


def list_sessions(device_id=None):
    """Lista sesiones, opcionalmente filtradas por device_id"""
    sessions = []
    if not os.path.exists(config.DATA_FOLDER):
        return sessions
    for filename in os.listdir(config.DATA_FOLDER):
        if filename.startswith('session_') and filename.endswith('.db'):
            session_id = filename[8:-3]
            try:
                conn = get_db(session_id)
                meta = conn.execute('SELECT * FROM session_meta WHERE id = 1').fetchone()
                t2_count = conn.execute('SELECT COUNT(*) FROM tabla2').fetchone()[0]
                t3_count = conn.execute('SELECT COUNT(*) FROM tabla3').fetchone()[0]
                # Obtener fechas de tabla1
                tabla1 = conn.execute('SELECT fecultprb, fecprbact FROM tabla1 LIMIT 1').fetchone()
                fecultprb = tabla1['fecultprb'] if tabla1 and tabla1['fecultprb'] else None
                fecprbact = tabla1['fecprbact'] if tabla1 and tabla1['fecprbact'] else None
                conn.close()
                if meta:
                    # Obtener device_id de la sesion (puede ser None en sesiones antiguas)
                    session_device_id = None
                    try:
                        session_device_id = meta['device_id']
                    except (IndexError, KeyError):
                        pass

                    # Filtrar por device_id si se especifica
                    if device_id and session_device_id and session_device_id != device_id:
                        continue

                    sessions.append({
                        'session_id': session_id,
                        'prefix_code': meta['prefix_code'],
                        'farm_name': meta['farm_name'],
                        'created_at': meta['created_at'],
                        'status': meta['status'],
                        'tabla2_count': t2_count,
                        'tabla3_count': t3_count,
                        'device_id': session_device_id,
                        'fecultprb': fecultprb,
                        'fecprbact': fecprbact,
                    })
            except Exception:
                continue
    sessions.sort(key=lambda s: s['created_at'], reverse=True)
    return sessions


def session_exists_by_prefix(prefix_code, device_id=None):
    """Verifica si ya existe una sesion con el mismo codigo de hato"""
    sessions = list_sessions(device_id=device_id)
    for s in sessions:
        if s['prefix_code'] == prefix_code:
            return True, s['farm_name']
    return False, None


def set_session_device(session_id, device_id):
    """Asocia una sesion con un device_id"""
    try:
        conn = get_db(session_id)
        # Intentar agregar columna si no existe (para bases de datos existentes)
        try:
            conn.execute('ALTER TABLE session_meta ADD COLUMN device_id TEXT')
        except:
            pass
        conn.execute('UPDATE session_meta SET device_id = ? WHERE id = 1', (device_id,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def delete_session(session_id):
    db_path = get_db_path(session_id)
    if os.path.exists(db_path):
        os.remove(db_path)
