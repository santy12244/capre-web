# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Run the application (localhost:5000, debug mode)
python app.py

# Install dependencies
venv/Scripts/pip.exe install -r requirements.txt

# Setup virtual environment (if needed)
python -m venv venv
```

## Architecture

**CAPRE** (Gestión de Hato Ganadero) is a Flask application for dairy cattle herd management that imports/exports DBF files and stores data in per-session SQLite databases.

### Flask Blueprints

- **main.bp** (`routes/main.py`) - Session lifecycle: select, list, delete sessions
- **upload.bp** (`routes/upload.py`) - DBF file import/export operations
- **principal.bp** (`routes/principal.py`) - Main CRUD operations for livestock data (services, births, milking, exits, health records)

### Database Structure

Each session creates a separate SQLite database (`data/session_{id}.db`) with:

- **session_meta** - Session metadata (farm prefix, name, status)
- **tabla1** - Farm/herd metadata (validation dates, milk totals, 59 fields)
- **tabla2** - Main livestock records (adult animals: identifiers, reproduction, health, production)
- **tabla3** - Young livestock/heifers (same structure as tabla2)

### Services Layer

- `services/dbf_import.py` - DBF to SQLite conversion with encoding handling (latin-1)
- `services/dbf_export.py` - SQLite to DBF export with custom binary format writing
- `services/file_utils.py` - DBF filename validation and parsing

### Key Domain Logic

- **125-day rule**: Minimum days after birth before service registration allowed
- **152-day gestation**: Minimum for miscarriage/abortion tracking
- **365-day threshold**: Heifers must be 365+ days old for service registration
- Animal identifiers use format: `SIIGG` (S=sex, II=year, GG=sequence)

## Code Conventions

- Spanish language UI, comments, and variable names
- Date format: DD/MES/AAAA (custom Jinja filter in app.py)
- Routes return JSON for AJAX operations, render templates for page loads
- Form validation happens both client-side (JavaScript) and server-side (Flask)

## DBF File Structure

The system expects three DBF files with naming pattern `{XX}_{YYYY}_{name}_{table}.dbf`:
- `*_tabla1.dbf` - Farm metadata
- `*_tabla2.dbf` - Adult animals
- `*_tabla3.dbf` - Heifers/young animals
