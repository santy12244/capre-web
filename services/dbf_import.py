import uuid
import datetime
from dbfread import DBF

from models.database import (
    init_db, get_db, TABLA1_FIELDS, ANIMAL_FIELDS
)


def _convert_value(value):
    """Convert a dbfread value to a SQLite-compatible value."""
    if value is None:
        return None
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, str):
        return value.strip()
    return value


def _import_table(conn, dbf_path, table_name, fields, encoding='latin-1'):
    """Read a .dbf file and insert all records into the given SQLite table."""
    dbf = DBF(dbf_path, encoding=encoding, ignore_missing_memofile=True)

    placeholders = ', '.join(['?'] * len(fields))
    columns = ', '.join(fields)
    sql = f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})'

    # Batch insert para mejor rendimiento
    BATCH_SIZE = 500
    batch = []
    count = 0

    for record in dbf:
        values = tuple(
            _convert_value(record.get(field.upper(), None))
            for field in fields
        )
        batch.append(values)
        count += 1

        if len(batch) >= BATCH_SIZE:
            conn.executemany(sql, batch)
            batch = []

    # Insertar registros restantes
    if batch:
        conn.executemany(sql, batch)

    conn.commit()
    return count


def import_dbf_files(file_paths, prefix_code):
    """Import 3 .dbf files into a new SQLite session.

    Args:
        file_paths: dict with keys 1, 2, 3 mapping to file paths
        prefix_code: the farm prefix (e.g. '05_0111')

    Returns:
        session_id (str)
    """
    session_id = uuid.uuid4().hex[:12]
    conn = init_db(session_id)

    try:
        # Import tabla1
        count1 = _import_table(conn, file_paths[1], 'tabla1', TABLA1_FIELDS)

        # Get farm name from tabla1
        row = conn.execute('SELECT nombre FROM tabla1 LIMIT 1').fetchone()
        farm_name = row['nombre'] if row else 'Sin nombre'

        # Import tabla2 and tabla3
        count2 = _import_table(conn, file_paths[2], 'tabla2', ANIMAL_FIELDS)
        count3 = _import_table(conn, file_paths[3], 'tabla3', ANIMAL_FIELDS)

        # Save session metadata
        conn.execute(
            'INSERT INTO session_meta (id, prefix_code, farm_name) VALUES (1, ?, ?)',
            (prefix_code, farm_name)
        )
        conn.commit()

        return session_id, {
            'tabla1': count1,
            'tabla2': count2,
            'tabla3': count3,
            'farm_name': farm_name,
        }

    except Exception:
        conn.close()
        # Clean up the database file on error
        from models.database import delete_session
        delete_session(session_id)
        raise
    finally:
        conn.close()
