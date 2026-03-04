"""
services/helpers.py
Utilidades compartidas para CAPRE: constantes de dominio, formateo de fechas
y validaciones reutilizables.
"""
from datetime import datetime
from flask import session as flask_session

# ── Constantes de dominio ─────────────────────────────────────────────────────

MESES = ('ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN',
         'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC')

ESTADO_MAP = {
    '0': 'Ternera',
    '1': 'Vaca parida',
    '2': 'Novilla parida',
    '3': 'Ing. seca',
    '4': 'Ing. produccion',
    '5': 'Aborto',
    '6': 'Seca',
}

ESTADO_COLOR = {
    '0': 'secondary',
    '1': 'success',
    '2': 'success',
    '3': 'warning',
    '4': 'info',
    '5': 'danger',
    '6': 'dark',
}

PAC_MAP = {'A': 'Abierta', 'P': 'Preñada'}
PAC_COLOR = {'A': 'danger', 'P': 'success'}

MAX_ORDENO_KG = 80.0
DIAS_MIN_SERVICIO = 125
DIAS_MIN_NOVILLA = 365
DIAS_MIN_ABORTO = 152

# ── Utilidades de sesión ─────────────────────────────────────────────────────

def get_session_id():
    """Retorna el session_id activo o None."""
    return flask_session.get('active_session_id')


# ── Formateo de fechas ───────────────────────────────────────────────────────

def format_fecha(fecha_str):
    """
    Convierte 'YYYY-MM-DD' → 'DD/MES/AAAA'.
    Retorna '—' si el valor está vacío o es inválido.
    """
    if not fecha_str:
        return '—'
    try:
        partes = str(fecha_str).split('-')
        if len(partes) == 3:
            anio, mes, dia = partes
            return f"{dia}/{MESES[int(mes) - 1]}/{anio}"
        return fecha_str
    except (ValueError, IndexError):
        return fecha_str or '—'


# ── Validaciones ─────────────────────────────────────────────────────────────

def parsear_ordeno(valor_raw):
    """
    Parsea un valor de ordeño normalizando coma/punto (teclados móviles).
    Retorna (float_o_None, mensaje_error_o_None).
    """
    if valor_raw is None:
        return None, None
    valor_str = str(valor_raw).replace(',', '.').strip()
    if not valor_str:
        return None, None
    try:
        valor = float(valor_str)
    except ValueError:
        return None, 'Valor no numerico'
    if valor > MAX_ORDENO_KG:
        return None, f'El valor de ordeño no puede superar {int(MAX_ORDENO_KG)} KG'
    return valor, None
