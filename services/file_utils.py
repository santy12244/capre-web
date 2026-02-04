import re


def detect_prefix(filename):
    """Extract prefix like '05_0111' from '05_0111_capre_tabla1.dbf'."""
    match = re.match(r'^(\d+_\d+)_capre_tabla[123]\.dbf$', filename, re.IGNORECASE)
    if match:
        return match.group(1)
    raise ValueError(f"Nombre de archivo no reconocido: {filename}")


def detect_table_number(filename):
    """Extract table number (1, 2, or 3) from filename."""
    match = re.search(r'tabla(\d)\.dbf$', filename, re.IGNORECASE)
    if match:
        return int(match.group(1))
    raise ValueError(f"No se pudo detectar el numero de tabla: {filename}")


def validate_upload_set(filenames):
    """Validate that we have exactly 3 files with matching prefix for tables 1, 2, 3.
    Returns the common prefix.
    """
    if len(filenames) != 3:
        raise ValueError("Se requieren exactamente 3 archivos .dbf")

    prefixes = set()
    tables_found = set()

    for fn in filenames:
        prefix = detect_prefix(fn)
        prefixes.add(prefix)
        table_num = detect_table_number(fn)
        tables_found.add(table_num)

    if len(prefixes) != 1:
        raise ValueError("Los archivos deben pertenecer a la misma finca (mismo prefijo)")

    if tables_found != {1, 2, 3}:
        raise ValueError("Se requieren los 3 archivos: tabla1, tabla2 y tabla3")

    return prefixes.pop()
