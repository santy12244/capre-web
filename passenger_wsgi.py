import sys
import os

# Ruta al virtualenv - ajustar si es necesario
INTERP = "/home4/holsteincol/public_html/capre-web/venv/bin/python3"
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.insert(0, '/home4/holsteincol/public_html/capre-web')
os.chdir('/home4/holsteincol/public_html/capre-web')

from app import create_app
application = create_app()
