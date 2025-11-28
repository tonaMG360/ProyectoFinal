from django.contrib import admin
from .models import Servicio, Doctor, Paciente

# Register your models here.


admin.site.register(Servicio)
admin.site.register(Doctor)
admin.site.register(Paciente)