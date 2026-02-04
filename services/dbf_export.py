import struct
import datetime
import os
from models.database import get_db, TABLA1_FIELDS, ANIMAL_FIELDS


def _get_dbf_field_type(value):
    """Determine DBF field type based on Python value."""
    if value is None:
        return 'C', 50  # Default character
    if isinstance(value, bool):
        return 'L', 1
    if isinstance(value, int):
        return 'N', 10
    if isinstance(value, float):
        return 'N', 12  # 12 chars with decimals
    if isinstance(value, (datetime.date, datetime.datetime)):
        return 'D', 8
    return 'C', 50  # Default to character


# Field definitions for DBF export (name, type, length, decimals)
TABLA1_DBF_FIELDS = [
    ('HATO', 'C', 10, 0),
    ('NOMBRE', 'C', 30, 0),
    ('PROPIETA', 'C', 30, 0),
    ('FECULTPRB', 'D', 8, 0),
    ('FECPRBACT', 'D', 8, 0),
    ('SUMLEC', 'N', 10, 0),
    ('ELABORAA', 'C', 20, 0),
]

ANIMAL_DBF_FIELDS = [
    ('CODINT', 'C', 10, 0),
    ('OREJERA', 'C', 10, 0),
    ('NOMBRE', 'C', 15, 0),
    ('REGISTRO', 'C', 15, 0),
    ('ESTADO', 'C', 1, 0),
    ('FECEST', 'D', 8, 0),
    ('ULTLEC', 'N', 6, 1),
    ('DIALEC', 'N', 4, 0),
    ('NUMSER', 'N', 3, 0),
    ('FECULTSER', 'D', 8, 0),
    ('PAC', 'C', 1, 0),
    ('NUMREB', 'N', 3, 0),
    ('FECSER', 'D', 8, 0),
    ('TORO', 'C', 15, 0),
    ('FECSECA', 'D', 8, 0),
    ('FECCHP', 'D', 8, 0),
    ('PANEW', 'C', 1, 0),
    ('FECPARTO', 'D', 8, 0),
    ('ORECRIA1', 'C', 10, 0),
    ('NOMCRIA1', 'C', 15, 0),
    ('SEXCRIA1', 'C', 1, 0),
    ('ORECRIA2', 'C', 10, 0),
    ('NOMCRIA2', 'C', 15, 0),
    ('SEXCRIA2', 'C', 1, 0),
    ('CART', 'C', 1, 0),
    ('FECSALE', 'D', 8, 0),
    ('MOTSALE', 'C', 1, 0),
    ('ORD1', 'N', 6, 1),
    ('ORD2', 'N', 6, 1),
    ('ORD3', 'N', 6, 1),
    ('TIPOPARTO', 'C', 1, 0),
    ('HACER1', 'C', 1, 0),
    ('HACER2', 'C', 1, 0),
    ('CALOR', 'C', 1, 0),
    ('NUEVO', 'N', 1, 0),
    ('CODTOR', 'C', 10, 0),
    ('CLASI', 'C', 5, 0),
    ('PTOS', 'N', 4, 0),
]


def _write_dbf_header(f, num_records, fields):
    """Write DBF file header."""
    # Calculate record length (1 byte deletion flag + sum of field lengths)
    record_length = 1 + sum(fld[2] for fld in fields)
    header_length = 32 + (len(fields) * 32) + 1

    # DBF header (32 bytes)
    now = datetime.datetime.now()
    header = struct.pack(
        '<BBBB I H H 20x',
        0x03,  # Version (dBASE III)
        now.year - 1900,  # Year
        now.month,
        now.day,
        num_records,
        header_length,
        record_length
    )
    f.write(header)

    # Field descriptors (32 bytes each)
    for name, ftype, length, decimals in fields:
        field_name = name.upper().encode('ascii')[:11].ljust(11, b'\x00')
        field_desc = struct.pack(
            '<11s c 4x B B 14x',
            field_name,
            ftype.encode('ascii'),
            length,
            decimals
        )
        f.write(field_desc)

    # Header terminator
    f.write(b'\x0D')


def _format_dbf_value(value, ftype, length, decimals):
    """Format a value for DBF field."""
    if value is None:
        if ftype == 'D':
            return b' ' * 8
        elif ftype == 'N':
            return b' ' * length
        elif ftype == 'L':
            return b' '
        else:
            return b' ' * length

    if ftype == 'D':
        # Date field: YYYYMMDD
        if isinstance(value, str) and value:
            try:
                dt = datetime.datetime.strptime(value, '%Y-%m-%d')
                return dt.strftime('%Y%m%d').encode('ascii')
            except ValueError:
                return b' ' * 8
        elif isinstance(value, (datetime.date, datetime.datetime)):
            return value.strftime('%Y%m%d').encode('ascii')
        return b' ' * 8

    elif ftype == 'N':
        # Numeric field
        if decimals > 0:
            formatted = f'{float(value or 0):{length}.{decimals}f}'
        else:
            formatted = f'{int(value or 0):>{length}d}'
        return formatted[:length].rjust(length).encode('ascii')

    elif ftype == 'L':
        # Logical field
        if value in (True, 1, 'T', 't', 'Y', 'y'):
            return b'T'
        elif value in (False, 0, 'F', 'f', 'N', 'n'):
            return b'F'
        return b' '

    else:
        # Character field
        text = str(value or '').encode('latin-1', errors='replace')
        return text[:length].ljust(length)


def _write_dbf_record(f, record, fields, sqlite_fields):
    """Write a single DBF record."""
    f.write(b' ')  # Deletion flag (space = not deleted)

    for i, (name, ftype, length, decimals) in enumerate(fields):
        sqlite_field = sqlite_fields[i]
        value = record[sqlite_field]
        f.write(_format_dbf_value(value, ftype, length, decimals))


def export_table_to_dbf(session_id, table_name, output_path, dbf_fields, sqlite_fields):
    """Export a SQLite table to a DBF file."""
    conn = get_db(session_id)

    # Get all records
    records = conn.execute(f'SELECT * FROM {table_name}').fetchall()
    conn.close()

    with open(output_path, 'wb') as f:
        _write_dbf_header(f, len(records), dbf_fields)

        for record in records:
            _write_dbf_record(f, record, dbf_fields, sqlite_fields)

        # End of file marker
        f.write(b'\x1A')


def export_all_tables(session_id, output_dir):
    """Export all 3 tables to DBF files.

    Returns:
        dict with file paths for tabla1, tabla2, tabla3
    """
    conn = get_db(session_id)

    # Get prefix code from session metadata
    meta = conn.execute('SELECT prefix_code FROM session_meta WHERE id = 1').fetchone()
    prefix = meta['prefix_code'] if meta else 'export'
    conn.close()

    os.makedirs(output_dir, exist_ok=True)

    # Export tabla1
    tabla1_path = os.path.join(output_dir, f'{prefix}_capre_tabla1.dbf')
    export_table_to_dbf(
        session_id, 'tabla1', tabla1_path,
        TABLA1_DBF_FIELDS,
        ['hato', 'nombre', 'propieta', 'fecultprb', 'fecprbact', 'sumlec', 'elaboraa']
    )

    # Export tabla2
    tabla2_path = os.path.join(output_dir, f'{prefix}_capre_tabla2.dbf')
    export_table_to_dbf(
        session_id, 'tabla2', tabla2_path,
        ANIMAL_DBF_FIELDS,
        [f.lower() for f, _, _, _ in ANIMAL_DBF_FIELDS]
    )

    # Export tabla3
    tabla3_path = os.path.join(output_dir, f'{prefix}_capre_tabla3.dbf')
    export_table_to_dbf(
        session_id, 'tabla3', tabla3_path,
        ANIMAL_DBF_FIELDS,
        [f.lower() for f, _, _, _ in ANIMAL_DBF_FIELDS]
    )

    # Get farm name for ZIP filename
    conn = get_db(session_id)
    hato = conn.execute('SELECT nombre FROM tabla1 LIMIT 1').fetchone()
    farm_name = hato['nombre'] if hato else 'HATO'
    # Clean farm name for filename (replace spaces with underscores, remove special chars)
    farm_name_clean = farm_name.replace(' ', '_').replace('/', '-').replace('\\', '-')
    conn.close()

    return {
        'tabla1': tabla1_path,
        'tabla2': tabla2_path,
        'tabla3': tabla3_path,
        'prefix': prefix,
        'farm_name': farm_name_clean
    }
