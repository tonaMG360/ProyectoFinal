import os
import sys
import pathlib

project_root = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Dentis.settings')

import django
django.setup()

from django.contrib.auth.models import User
from core.models import Paciente

print('Starting link script: attempting to link existing Paciente records to User objects...')

linked = []
skipped = []

for p in Paciente.objects.filter(user__isnull=True):
    nombre = (p.nombre or '').strip()
    if not nombre:
        skipped.append((p.id, 'no-name'))
        continue
    # Try exact username match
    try:
        user = User.objects.get(username__iexact=nombre)
        p.user = user
        p.save()
        linked.append((p.id, user.username, 'username'))
        continue
    except User.DoesNotExist:
        pass

    # Try matching first + last
    try:
        user = User.objects.get(first_name__iexact=nombre.split(' ')[0], last_name__iexact=' '.join(nombre.split(' ')[1:]) if len(nombre.split(' '))>1 else '')
        p.user = user
        p.save()
        linked.append((p.id, user.username, 'first_last'))
        continue
    except User.DoesNotExist:
        pass

    # Try matching full name combination
    fullnames = [f"{u.first_name} {u.last_name}".strip() for u in User.objects.exclude(first_name='', last_name='')]
    matched_user = None
    for u in User.objects.exclude(first_name='', last_name=''):
        if u.get_full_name().strip().lower() == nombre.lower():
            matched_user = u
            break
    if matched_user:
        p.user = matched_user
        p.save()
        linked.append((p.id, matched_user.username, 'full_name'))
        continue

    skipped.append((p.id, 'no-match'))

print('\nLinked:')
for r in linked:
    print('Paciente id', r[0], '-> user', r[1], 'by', r[2])

print('\nSkipped:')
for s in skipped:
    print('Paciente id', s[0], 'reason=', s[1])

print('\nDone.')
python manage.py runserver