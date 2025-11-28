"""
URL configuration for Dentis project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from core import views
from core.forms import PatientLoginForm
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls), # Panel de administrador por defecto de Django
    path('', views.inicio, name='inicio'),
    path('productos/', views.productos, name='productos'),
    path('nosotros/', views.nosotros, name='nosotros'),
    path('doctores/', views.doctores, name='doctores'),
    path('doctores/<int:pk>/', views.doctor_detail, name='doctor_detail'),
    path('pacientes/login/', auth_views.LoginView.as_view(template_name='core/login_pacientes.html', authentication_form=PatientLoginForm), name='login_pacientes'),
    path('pacientes/register/', views.register_paciente, name='register_paciente'),
    path('citas/nueva/', views.crear_cita, name='crear_cita'),
    path('citas/mis/', views.mis_citas, name='mis_citas'),
    path('citas/pendientes/', views.citas_pendientes, name='citas_pendientes'),
    path('citas/<int:pk>/editar/', views.editar_cita, name='editar_cita'),
    path('citas/<int:pk>/cancelar/', views.cancelar_cita, name='cancelar_cita'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

]
