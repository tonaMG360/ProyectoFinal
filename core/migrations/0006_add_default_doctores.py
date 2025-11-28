"""Data migration: add default doctors for booking (at least 4).

Creates doctor entries only if they do not already exist (idempotent).
"""
from django.db import migrations


def create_default_doctores(apps, schema_editor):
    Doctor = apps.get_model('core', 'Doctor')
    doctores = [
        {
            'nombre': 'Dra. Ana López',
            'especialidad': 'Ortodoncia',
            'experiencia': '8 años',
            'disponible_desde': '09:00:00',
            'disponible_hasta': '17:00:00',
        },
        {
            'nombre': 'Dr. Carlos Márquez',
            'especialidad': 'Endodoncia',
            'experiencia': '10 años',
            'disponible_desde': '08:00:00',
            'disponible_hasta': '16:00:00',
        },
        {
            'nombre': 'Dra. Marta Ruiz',
            'especialidad': 'Implantes',
            'experiencia': '6 años',
            'disponible_desde': '10:00:00',
            'disponible_hasta': '18:00:00',
        },
        {
            'nombre': 'Dr. José Fernández',
            'especialidad': 'Medicina general dental',
            'experiencia': '12 años',
            'disponible_desde': '07:30:00',
            'disponible_hasta': '15:30:00',
        },
    ]

    for d in doctores:
        exists = Doctor.objects.filter(nombre__iexact=d['nombre']).exists()
        if not exists:
            # Model TimeField accepts strings in migration context
            Doctor.objects.create(**d)


def remove_default_doctores(apps, schema_editor):
    Doctor = apps.get_model('core', 'Doctor')
    nombres = ['Dra. Ana López', 'Dr. Carlos Márquez', 'Dra. Marta Ruiz', 'Dr. José Fernández']
    Doctor.objects.filter(nombre__in=nombres).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_cita_duracion_doctor_disponible_desde_and_more'),
    ]

    operations = [
        migrations.RunPython(create_default_doctores, reverse_code=remove_default_doctores),
    ]
