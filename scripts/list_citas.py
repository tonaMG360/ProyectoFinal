import os, sys, pathlib
project_root = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','Dentis.settings')
import django
django.setup()
from core.models import Cita
print('Citas count=', Cita.objects.count())
for c in Cita.objects.all():
    print('-', c.servicio.titulo, c.paciente.nombre, c.fecha_hora, c.estado)
