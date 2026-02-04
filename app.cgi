#!/home4/holsteincol/public_html/capre-web/venv/bin/python3
# -*- coding: utf-8 -*-

import sys
import os

# Agregar el directorio de la aplicación al path
sys.path.insert(0, '/home4/holsteincol/public_html/capre-web')
os.chdir('/home4/holsteincol/public_html/capre-web')

from wsgiref.handlers import CGIHandler
from app import create_app

application = create_app()

# Deshabilitar buffering para CGI
CGIHandler().run(application)
