
from django.test import TestCase
from django.utils import timezone
from .models import Paciente, Servicio, Doctor, Cita
from .forms import CitaForm
import datetime


class TestModels(TestCase):

	def test_citas_pendientes_view(self):
		from django.contrib.auth.models import User
		from django.test import Client
		# Crear usuario y paciente
		user = User.objects.create_user(username='pendiente', password='pass123')
		pac = Paciente.objects.create(nombre='Pendiente', edad=30, historial_medico='', user=user)
		doc = Doctor.objects.create(nombre='Dr Test', especialidad='General', experiencia='5 años')
		svc = Servicio.objects.create(titulo='TestSvc', descripcion='Desc', precio=100, duracion=30, icono='test')
		# Crear cita pendiente y otra confirmada
		now = timezone.now()
		Cita.objects.create(paciente=pac, servicio=svc, doctor=doc, fecha_hora=now, duracion=30, estado='PENDING')
		Cita.objects.create(paciente=pac, servicio=svc, doctor=doc, fecha_hora=now, duracion=30, estado='CONFIRMED')
		c = Client()
		c.force_login(user)
		r = c.get('/citas/pendientes/')
		self.assertEqual(r.status_code, 200)
		html = r.content.decode('utf-8')
		self.assertIn('Citas Pendientes', html)
		self.assertIn('Pendiente', html)
		self.assertNotIn('Confirmada', html)
	def test_sample(self):
		self.assertEqual(1+1, 2)

	def test_doctor_overlap_prevented(self):
		# create doctor and paciente and servicio
		doc = Doctor.objects.create(nombre='Dr Test', especialidad='General', experiencia='5 años', disponible_desde=datetime.time(9,0), disponible_hasta=datetime.time(17,0))
		svc = Servicio.objects.create(titulo='TestSvc', descripcion='Desc', precio=100, duracion=30, icono='test')
		pac = Paciente.objects.create(nombre='Paciente Test', edad=30, historial_medico='')

		# existing appointment at 10:00 for 30 mins
		start = timezone.now() + datetime.timedelta(days=1)
		start = start.replace(hour=10, minute=0, second=0, microsecond=0)
		Cita.objects.create(paciente=pac, servicio=svc, doctor=doc, fecha_hora=start, duracion=30)

		# attempt to create overlapping appointment (10:15 for 30) should be invalid
		form_data = {'servicio': svc.id, 'doctor': doc.id, 'duracion': 30, 'fecha': start.date().isoformat(), 'hora': '10:15', 'telefono': '', 'notas': ''}
		form = CitaForm(data=form_data, paciente=pac)
		self.assertFalse(form.is_valid())

	def test_slot_non_overlapping(self):
		doc = Doctor.objects.create(nombre='Dr Free', especialidad='General', experiencia='5 años', disponible_desde=datetime.time(9,0), disponible_hasta=datetime.time(17,0))
		svc = Servicio.objects.create(titulo='TestSvc2', descripcion='Desc', precio=100, duracion=60, icono='test')
		pac = Paciente.objects.create(nombre='Paciente2', edad=22, historial_medico='')
		start = timezone.now() + datetime.timedelta(days=2)
		start = start.replace(hour=9, minute=0, second=0, microsecond=0)
		Cita.objects.create(paciente=pac, servicio=svc, doctor=doc, fecha_hora=start, duracion=60)

		# booking at 10:00 (non-overlapping) should be valid
		form_data = {'servicio': svc.id, 'doctor': doc.id, 'duracion': 60, 'fecha': start.date().isoformat(), 'hora': '10:00', 'telefono': '', 'notas': ''}
		form = CitaForm(data=form_data, paciente=pac)
		self.assertTrue(form.is_valid())

	def test_doctor_availability_window(self):
		doc = Doctor.objects.create(nombre='Dr Busy', especialidad='Gent', experiencia='10 años', disponible_desde=datetime.time(9,0), disponible_hasta=datetime.time(10,0))
		svc = Servicio.objects.create(titulo='Short', descripcion='Desc', precio=100, duracion=30, icono='test')
		pac = Paciente.objects.create(nombre='P3', edad=30, historial_medico='')
		# try to book at 08:30 -> should fail due to doctor's availability
		date = (timezone.now() + datetime.timedelta(days=2)).date().isoformat()
		form_data = {'servicio': svc.id, 'doctor': doc.id, 'duracion': 30, 'fecha': date, 'hora': '08:30', 'telefono': '', 'notas': ''}
		form = CitaForm(data=form_data, paciente=pac)
		self.assertFalse(form.is_valid())

	def test_auto_assign_doctor_in_view(self):
		# integration style test: create two doctors, create user and use client to post a new appointment without picking doctor
		from django.contrib.auth.models import User
		client_user = User.objects.create_user(username='user_assign', password='pass123')
		d1 = Doctor.objects.create(nombre='Dr A', especialidad='G', experiencia='2y', disponible_desde=datetime.time(9,0), disponible_hasta=datetime.time(18,0))
		d2 = Doctor.objects.create(nombre='Dr B', especialidad='G', experiencia='3y', disponible_desde=datetime.time(9,0), disponible_hasta=datetime.time(18,0))
		svc = Servicio.objects.create(titulo='SlotSvc', descripcion='Desc', precio=100, duracion=30, icono='test')
		# register paciente and link user
		pac = Paciente.objects.create(nombre='AssignUser', edad=30, historial_medico='', user=client_user)
		# login client
		from django.test import Client
		c = Client()
		c.force_login(client_user)
		fecha = (timezone.now() + datetime.timedelta(days=3)).date().isoformat()
		resp = c.post('/citas/nueva/', {'servicio': svc.id, 'fecha': fecha, 'hora': '09:00', 'duracion': 30}, follow=True)
		self.assertEqual(resp.status_code, 200)
		# check that a Cita was created and doctor assigned
		cita = Cita.objects.filter(paciente__user=client_user).first()
		self.assertIsNotNone(cita)
		self.assertIsNotNone(cita.doctor)

	def test_productos_public_access(self):
		# unauthenticated users should be able to view products (200)
		from django.test import Client
		c = Client()
		r = c.get('/productos/')
		self.assertEqual(r.status_code, 200)

	def test_default_doctors_exist_and_available(self):
		# The new data migration should have created at least 4 doctors with availability windows.
		qs = Doctor.objects.all()
		self.assertGreaterEqual(qs.count(), 4, 'Se esperaban al menos 4 doctores por defecto')
		# Ensure each has availability times set
		for d in qs:
			# disponibilidad fields may be None for some custom doctors, but our seeded doctors should have times
			self.assertIsNotNone(d.disponible_desde, f'Doctor {d} debe tener disponible_desde configurado')
			self.assertIsNotNone(d.disponible_hasta, f'Doctor {d} debe tener disponible_hasta configurado')

	def test_productos_authenticated(self):
		# authenticated user should see products (200)
		from django.contrib.auth.models import User
		from django.test import Client
		user = User.objects.create_user(username='viewer', password='pass123')
		c = Client()
		c.force_login(user)
		r = c.get('/productos/')
		self.assertEqual(r.status_code, 200)

	def test_nav_agendar_link_present(self):
		# The navbar should include a link to create appointment
		from django.test import Client
		c = Client()
		r = c.get('/')
		self.assertEqual(r.status_code, 200)
		self.assertIn('/citas/nueva/', r.content.decode('utf-8'))

	def test_reserve_link_requires_login_when_anonymous(self):
		# On productos page, anonymous users should get a link to login with next that points to the create page
		from django.test import Client
		c = Client()
		r = c.get('/productos/')
		html = r.content.decode('utf-8')
		# Reserve link should point to crear_cita (which will ask login when clicked)
		self.assertIn('/citas/nueva/?servicio_id=', html)

	def test_doctores_list_public(self):
		from django.test import Client
		# Should return 200 and contain at least one doctor's name from the seeded data
		c = Client()
		r = c.get('/doctores/')
		self.assertEqual(r.status_code, 200)
		content = r.content.decode('utf-8')
		# seeded doctor 'Dra. Ana López' should appear
		self.assertIn('Dra. Ana López', content)

	def test_doctores_filter_by_specialty(self):
		from django.test import Client
		c = Client()
		# filter for 'Ortodoncia' which should return Dra. Ana López but not others
		r = c.get('/doctores/?especialidad=Ortodoncia')
		self.assertEqual(r.status_code, 200)
		html = r.content.decode('utf-8')
		self.assertIn('Dra. Ana López', html)
		# a doctor with the 'Implantes' specialty (Dra. Marta Ruiz) should not appear
		self.assertNotIn('Dra. Marta Ruiz', html)

	def test_doctor_reserve_link_prefill(self):
		from django.test import Client
		c = Client()
		r = c.get('/doctores/')
		html = r.content.decode('utf-8')
		# Each doctor card includes a Reservar link to crear_cita with doctor id
		self.assertIn('/citas/nueva/?doctor=', html)

	def test_doctor_profile_page_shows_info(self):
		from django.test import Client
		c = Client()
		# pick a seeded doctor id by name
		d = Doctor.objects.filter(nombre__icontains='Ana').first()
		self.assertIsNotNone(d)
		r = c.get(f'/doctores/{d.id}/')
		self.assertEqual(r.status_code, 200)
		h = r.content.decode('utf-8')
		self.assertIn(d.nombre, h)
		self.assertIn('Reservar con este doctor', h)

	def test_crear_cita_redirects_with_message_for_anonymous(self):
		# Should redirect anonymous user to login AND show a helpful message
		from django.test import Client
		c = Client()
		r = c.get('/citas/nueva/?servicio_id=1', follow=True)
		# final landing page should be login page
		self.assertIn('/pacientes/login/', r.request['PATH_INFO'])
		content = r.content.decode('utf-8')
		self.assertIn('Necesitas iniciar sesión para agendar una cita.', content)
