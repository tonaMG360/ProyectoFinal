"""Add bio and foto_url fields to Doctor model and seed sample bios for existing doctors.

This migration is idempotent — it adds the two fields and updates seeded doctors with sample bios
if present.
"""
from django.db import migrations, models


def add_sample_bios(apps, schema_editor):
    Doctor = apps.get_model('core', 'Doctor')
    samples = {
        'Dra. Ana López': 'Especialista en ortodoncia con 8 años de experiencia en tratamientos estéticos y funcionales.',
        'Dr. Carlos Márquez': 'Endodoncista con amplia trayectoria en tratamientos de conducto y conservación dental.',
        'Dra. Marta Ruiz': 'Experta en implantes y rehabilitación protésica, con enfoque en comodidad del paciente.',
        'Dr. José Fernández': 'Médico dental general con 12 años de experiencia en diagnóstico integral y prevención.'
    }
    for nombre, bio in samples.items():
        try:
            d = Doctor.objects.filter(nombre__iexact=nombre).first()
            if d and not d.bio:
                d.bio = bio
                # set a placeholder photo URL to keep UI pleasant; users can change later
                if not d.foto_url:
                    d.foto_url = '/static/images/doctor_placeholder.png'
                d.save()
        except Exception:
            continue


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_add_default_doctores'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctor',
            name='bio',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='doctor',
            name='foto_url',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.RunPython(add_sample_bios, reverse_code=migrations.RunPython.noop),
    ]
