import os
import sys
import pathlib
project_root = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','Dentis.settings')
import django
django.setup()
from core.models import Servicio
print('Servicios count=', Servicio.objects.count())
for s in Servicio.objects.all():
    print('-', s.titulo, s.precio, 'icono=', s.icono)
