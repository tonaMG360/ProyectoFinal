import os
import sys
import pathlib
import django

# Make sure project root is on sys.path when running this script from scripts/
project_root = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Dentis.settings')
django.setup()

from django.test import Client

paths = ['/', '/productos/', '/nosotros/', '/pacientes/login/', '/pacientes/register/']
for p in paths:
	r = Client().get(p, HTTP_HOST='127.0.0.1')
	print('\n---', p, 'status_code=', r.status_code)
	# print a short preview so we can verify the template renders
	print(r.content.decode('utf-8')[:600])

# Quick functional test: register a new patient and verify redirect + logged-in view
import random
u = f"testuser{random.randint(1000,9999)}"
data = {
	'username': u,
	'email': f'{u}@example.com',
	'first_name': 'Test',
	'last_name': 'Paciente',
	'password1': 'ComplexPass123!',
	'password2': 'ComplexPass123!'
}
client = Client()
resp = client.post('/pacientes/register/', data, HTTP_HOST='127.0.0.1')
print('\n--- POST /pacientes/register/ status_code=', resp.status_code)
if resp.status_code in (302, 301):
	print('Redirected to:', resp['Location'])
	# now get login page (should show dashboard since view logs us in)
	r2 = client.get('/pacientes/login/', HTTP_HOST='127.0.0.1')
	print('/pacientes/login/ after register status=', r2.status_code)
	print(r2.content.decode('utf-8')[:400])
else:
	print('Register page response (short):', resp.content.decode('utf-8')[:400])

# Create an appointment for the newly-registered user (requires authentication)
from core.models import Servicio
svc = Servicio.objects.first()
if svc:
	import datetime
	fecha = (datetime.date.today() + datetime.timedelta(days=random.randint(2, 10))).isoformat()
	hora = '10:30'
	appt_data = {'servicio': str(svc.id), 'fecha': fecha, 'hora': hora, 'telefono': '5551234567', 'notas': 'Prueba de reserva'}
	r_appt = client.post('/citas/nueva/', appt_data, HTTP_HOST='127.0.0.1')
	print('\n--- POST /citas/nueva/ status_code=', r_appt.status_code)
	if r_appt.status_code in (301,302):
		print('Created appointment; redirected to', r_appt['Location'])
		# fetch list
		r_mis = client.get('/citas/mis/', HTTP_HOST='127.0.0.1')
		print('/citas/mis/ status=', r_mis.status_code)
		print(r_mis.content.decode('utf-8')[:600])
		# Find the appointment created for this user and try to edit it
		from core.models import Cita
		appt = Cita.objects.filter(paciente__user__username=u).order_by('-id').first()
		if appt:
			print('\nFound appt id', appt.id)
			# try to update the appointment to one day later at 11:00
			import datetime
			new_date = (appt.fecha_hora.date() + datetime.timedelta(days=1)).isoformat()
			new_time = '11:00'
			edit_data = {'servicio': str(appt.servicio.id), 'fecha': new_date, 'hora': new_time, 'telefono': appt.telefono or '', 'notas': 'Modificada desde test'}
			r_edit = client.post(f'/citas/{appt.id}/editar/', edit_data, HTTP_HOST='127.0.0.1')
			print('/citas/<id>/editar/ status=', r_edit.status_code)
			# now cancel it
			r_cancel = client.post(f'/citas/{appt.id}/cancelar/', HTTP_HOST='127.0.0.1')
			print('/citas/<id>/cancelar/ status=', r_cancel.status_code)
	else:
		print('Appointment creation response preview:', r_appt.content.decode('utf-8')[:600])
else:
	print('No servicio found to create appointment')
