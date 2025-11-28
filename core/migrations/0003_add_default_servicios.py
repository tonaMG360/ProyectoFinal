"""Data migration: add 8 common dentistry services as initial content.

This creates entries only if they don't already exist (idempotent).
"""
from django.db import migrations


def create_default_servicios(apps, schema_editor):
    Servicio = apps.get_model('core', 'Servicio')
    from decimal import Decimal

    servicios = [
        {
            'titulo': 'Limpieza dental',
            'descripcion': 'Profilaxis y limpieza profesional para eliminar placa, sarro y manchas.',
            'precio': Decimal('500.00'),
            'icono': 'cleaning'
        },
        {
            'titulo': 'Empaste (Obturación)',
            'descripcion': 'Tratamiento restaurador para caries con resina compuesta o amalgama.',
            'precio': Decimal('900.00'),
            'icono': 'filling'
        },
        {
            'titulo': 'Endodoncia (tratamiento de conducto)',
            'descripcion': 'Tratamiento para salvar dientes con pulpa infectada o inflamada.',
            'precio': Decimal('2500.00'),
            'icono': 'root_canal'
        },
        {
            'titulo': 'Extracción dental',
            'descripcion': 'Extracción simple o quirúrgica de piezas dentales dañadas o retenidas.',
            'precio': Decimal('700.00'),
            'icono': 'extraction'
        },
        {
            'titulo': 'Ortodoncia (brackets)',
            'descripcion': 'Tratamientos de alineamiento dental con brackets o alineadores.',
            'precio': Decimal('12000.00'),
            'icono': 'braces'
        },
        {
            'titulo': 'Implantes dentales',
            'descripcion': 'Colocación de implantes de titanio y prótesis sobre implantes.',
            'precio': Decimal('15000.00'),
            'icono': 'implant'
        },
        {
            'titulo': 'Blanqueamiento dental',
            'descripcion': 'Procedimiento de blanqueamiento profesional en clínica o en casa supervisado.',
            'precio': Decimal('2000.00'),
            'icono': 'whitening'
        },
        {
            'titulo': 'Prótesis y coronas',
            'descripcion': 'Coronas, puentes y prótesis parciales o totales para restaurar la función y estética.',
            'precio': Decimal('8000.00'),
            'icono': 'crown'
        },
    ]

    for s in servicios:
        # create only if nothing similar exists to avoid duplicates
        exists = Servicio.objects.filter(titulo__iexact=s['titulo']).exists()
        if not exists:
            Servicio.objects.create(**s)


def remove_default_servicios(apps, schema_editor):
    Servicio = apps.get_model('core', 'Servicio')
    titulos = [
        'Limpieza dental',
        'Empaste (Obturación)',
        'Endodoncia (tratamiento de conducto)',
        'Extracción dental',
        'Ortodoncia (brackets)',
        'Implantes dentales',
        'Blanqueamiento dental',
        'Prótesis y coronas',
    ]
    Servicio.objects.filter(titulo__in=titulos).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_paciente_user'),
    ]

    operations = [
        migrations.RunPython(create_default_servicios, reverse_code=remove_default_servicios),
    ]
