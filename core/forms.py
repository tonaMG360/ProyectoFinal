from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class PatientLoginForm(AuthenticationForm):
	"""AuthenticationForm subclass to style widgets for Tailwind + Spanish labels."""
	username = forms.CharField(
		label="Usuario o Correo",
		widget=forms.TextInput(attrs={
			'class': 'block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
			'placeholder': 'ejemplo@correo.com'
		})
	)

	password = forms.CharField(
		label="Contraseña",
		strip=False,
		widget=forms.PasswordInput(attrs={
			'class': 'block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
			'placeholder': '••••••••'
		})
	)


class PatientRegistrationForm(UserCreationForm):
	"""Register patients using the built-in User model.

	Minimal fields: username, email, first_name, last_name, password1, password2
	On save, returns the created User instance.
	"""
	email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'block w-full px-3 py-2 border rounded-lg', 'placeholder': 'ejemplo@correo.com'}))
	first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'block w-full px-3 py-2 border rounded-lg', 'placeholder': 'Nombre'}))
	last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'block w-full px-3 py-2 border rounded-lg', 'placeholder': 'Apellido'}))

	class Meta:
		model = User
		fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

	def save(self, commit=True):
		user = super().save(commit=False)
		user.email = self.cleaned_data['email']
		user.first_name = self.cleaned_data.get('first_name', '')
		user.last_name = self.cleaned_data.get('last_name', '')
		if commit:
			user.save()
		return user


from django.forms import ModelForm, DateField, TimeField, DateInput, TimeInput
from .models import Cita, Servicio
from django import forms


class CitaForm(forms.ModelForm):
	# Provide separate date and time inputs for easier UI handling
	fecha = DateField(widget=DateInput(attrs={'type': 'date', 'class': 'block w-full px-3 py-2 border rounded-lg'}))
	hora = TimeField(widget=TimeInput(attrs={'type': 'time', 'class': 'block w-full px-3 py-2 border rounded-lg'}))

	class Meta:
		model = Cita
		fields = ['servicio', 'doctor', 'duracion', 'fecha', 'hora', 'telefono', 'notas']
		widgets = {
			'servicio': forms.Select(attrs={'class': 'block w-full px-3 py-2 border rounded-lg'}),
			'doctor': forms.Select(attrs={'class': 'block w-full px-3 py-2 border rounded-lg'}),
			'duracion': forms.Select(attrs={'class': 'block w-full px-3 py-2 border rounded-lg'}),
			'telefono': forms.TextInput(attrs={'class': 'block w-full px-3 py-2 border rounded-lg', 'placeholder': 'Teléfono (opcional)'}),
			'notas': forms.Textarea(attrs={'class': 'block w-full px-3 py-2 border rounded-lg', 'rows':3, 'placeholder':'Notas sobre la cita (opcional)'}),
		}

	def __init__(self, *args, paciente=None, **kwargs):
		# Accept paciente as optional for validation checks (owner)
		self.paciente = paciente
		super().__init__(*args, **kwargs)


	def clean(self):
		cleaned = super().clean()
		fecha = cleaned.get('fecha')
		hora = cleaned.get('hora')
		if fecha and hora:
			import datetime
			dt = datetime.datetime.combine(fecha, hora)
			# make timezone-aware if project uses TIME_ZONE / USE_TZ
			from django.utils import timezone
			if timezone.is_naive(dt):
				try:
					dt = timezone.make_aware(dt)
				except Exception:
					# fallback, keep naive
					pass
			cleaned['fecha_hora'] = dt

			# Validation: datetime must be in the future
			from django.utils import timezone
			now = timezone.now()
			if dt <= now:
				raise forms.ValidationError('La fecha y hora deben ser en el futuro.')

			# Business hours: allow only between 09:00 and 18:00
			import datetime as _dt
			start = _dt.time(9, 0)
			end = _dt.time(18, 0)
			if not (start <= dt.time() <= end):
				raise forms.ValidationError('La cita debe reservarse dentro del horario de atención: 09:00 - 18:00.')

			# compute end time based on duracion or servicio default
			# prefer cita-level duracion passed in cleaned data
			dur = cleaned.get('duracion')
			if not dur and cleaned.get('servicio'):
				dur = cleaned.get('servicio').duracion
			if not dur:
				dur = 30

			import datetime as _dt
			end_dt = dt + _dt.timedelta(minutes=int(dur))

			# Avoid double-booking for the same paciente at the same datetime
			from .models import Cita
			qs = Cita.objects.filter(fecha_hora__lt=end_dt, )
			if self.instance and self.instance.pk:
				qs = qs.exclude(pk=self.instance.pk)
			if self.paciente:
				existing_for_patient = qs.filter(paciente=self.paciente)
				conflict_p = False
				for ex in existing_for_patient:
					if ex.end_time > dt:
						conflict_p = True
						break
				if conflict_p:
					raise forms.ValidationError('Ya tienes una cita programada en ese intervalo.')

			# If a doctor is selected, check doctor availability and overlapping with other appointments for that doctor
			doctor = cleaned.get('doctor')
			if doctor:
				# check doctor's availability window
				if doctor.disponible_desde and doctor.disponible_hasta:
					if not (doctor.disponible_desde <= dt.time() <= doctor.disponible_hasta and doctor.disponible_desde <= end_dt.time() <= doctor.disponible_hasta):
						raise forms.ValidationError('El doctor seleccionado no está disponible en esa franja horaria.')

				# overlapping for doctor
				qs_doc = Cita.objects.filter(doctor=doctor, fecha_hora__lt=end_dt)
				if self.instance and self.instance.pk:
					qs_doc = qs_doc.exclude(pk=self.instance.pk)
				# check existing end times for overlap (existing.fecha_hora < new_end and existing.end >= new_start)
				overlap = False
				for existing in qs_doc:
					existing_end = existing.end_time
					if existing_end > dt:
						overlap = True
						break
				if overlap:
					raise forms.ValidationError('El doctor ya tiene otra cita en ese intervalo.')
		return cleaned

	def save(self, commit=True, paciente=None):
		# combine and save as Cita model
		cita = super().save(commit=False)
		if 'fecha_hora' in self.cleaned_data:
			cita.fecha_hora = self.cleaned_data['fecha_hora']
		if paciente is not None:
			cita.paciente = paciente
		if commit:
			cita.save()
		return cita

