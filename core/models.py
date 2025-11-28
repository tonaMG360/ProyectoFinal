from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Servicio(models.Model):
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    icono = models.CharField(max_length=50, default='smile') # Para mapear iconos en frontend
    # duration in minutes used when scheduling (default 30)
    DURATION_CHOICES = [(30, '30 minutos'), (60, '1 hora')]
    duracion = models.IntegerField(choices=DURATION_CHOICES, default=30)

    def __str__(self):
        return self.titulo

class Doctor(models.Model):
    nombre = models.CharField(max_length=100)
    especialidad = models.CharField(max_length=100)
    experiencia = models.CharField(max_length=100)
    # short biography and photo URL (optional) for public profile
    bio = models.TextField(blank=True, default='')
    foto_url = models.CharField(max_length=255, blank=True, default='')
    # daily availability window (simple model: same hours every day)
    disponible_desde = models.TimeField(null=True, blank=True, default=None)
    disponible_hasta = models.TimeField(null=True, blank=True, default=None)
    
    def __str__(self):
        return self.nombre
    
class Paciente(models.Model):
    nombre = models.CharField(max_length=100)
    # Link to the Django User (optional, introduced in migration)
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    edad = models.IntegerField()
    historial_medico = models.TextField()

    def __str__(self):
        return self.nombre 


class Cita(models.Model):
    ESTADO_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('CONFIRMED', 'Confirmada'),
        ('CANCELLED', 'Cancelada'),
        ('COMPLETED', 'Completada'),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='citas')
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT, related_name='citas')
    doctor = models.ForeignKey(Doctor, null=True, blank=True, on_delete=models.SET_NULL, related_name='citas')
    fecha_hora = models.DateTimeField()
    # duration in minutes (30 or 60). If not set, use servicio.duracion
    duracion = models.IntegerField(choices=[(30, '30 minutos'), (60, '1 hora')], null=True, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    notas = models.TextField(blank=True)
    estado = models.CharField(max_length=12, choices=ESTADO_CHOICES, default='PENDING')
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_hora']

    def __str__(self):
        return f"Cita {self.id} - {self.servicio.titulo} para {self.paciente.nombre} @ {self.fecha_hora} ({self.estado})"

    @property
    def end_time(self):
        """Calculate end time using duracion or servicio.duracion"""
        import datetime
        minutes = self.duracion if self.duracion else (self.servicio.duracion if self.servicio and hasattr(self.servicio, 'duracion') else 30)
        return self.fecha_hora + datetime.timedelta(minutes=minutes)