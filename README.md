# Dentis Arroyo — Sistema de Gestión de Citas Dentales

Este proyecto es una aplicación web desarrollada en Django para la gestión de citas, pacientes, doctores y servicios en una clínica dental.

## Funcionalidades principales

- **Página de inicio**: Presentación de la clínica y acceso rápido a las secciones principales.
- **Catálogo de servicios**: Visualización pública de los servicios dentales ofrecidos, con precios y descripciones.
- **Registro y login de pacientes**: Los pacientes pueden crear una cuenta y autenticarse para gestionar sus citas.
- **Agendar cita**: Los pacientes pueden reservar citas eligiendo servicio, fecha, hora y (opcionalmente) doctor preferido. El sistema valida disponibilidad y evita traslapes.
- **Listado de doctores**: Página pública con todos los doctores, filtro por especialidad, perfil individual con foto, bio y horario.
- **Perfil de doctor**: Detalle de cada doctor, con botón para agendar cita directamente con él.
- **Citas pendientes**: Vista exclusiva para pacientes autenticados donde pueden ver solo sus citas en estado "Pendiente".
- **Mis citas**: Listado de todas las citas del paciente, con opciones para editar o cancelar.
- **Confirmación y notificaciones**: Al agendar, editar o cancelar una cita, el paciente recibe confirmación (por email a Futuro, consola en local).
- **Validaciones avanzadas**: El sistema impide agendar fuera de horario, traslapes, y permite solo duraciones válidas (30/60 min).
- **Panel de administración**: Acceso para staff vía `/admin/` para gestionar usuarios, doctores, servicios y citas.

## Requisitos
- Python 3.11+
- Django 5.x
- SQLite (por defecto) o cualquier base soportada por Django
- (Opcional) Pillow si se habilita carga de fotos reales

## Instalación y uso rápido
1. Clona el repositorio y entra al directorio del proyecto.
2. Instala dependencias:
	```powershell
	pip install -r requirements.txt
	```
3. Aplica migraciones:
	```powershell
	python manage.py migrate
	```
4. (Opcional) Crea un superusuario:
	```powershell
	python manage.py createsuperuser
	```
5. Inicia el servidor:
	```powershell
	python manage.py runserver
	```
6. Accede a la app en [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Navegación principal
- `/` — Inicio
- `/productos/` — Servicios
- `/doctores/` — Listado de doctores
- `/doctores/<id>/` — Perfil de doctor
- `/pacientes/login/` — Login de pacientes
- `/pacientes/register/` — Registro de pacientes
- `/citas/nueva/` — Agendar cita
- `/citas/pendientes/` — Citas pendientes del paciente
- `/citas/mis/` — Todas las citas del paciente
- `/admin/` — Panel administrativo

## Notas
- El sistema incluye datos de ejemplo: 8 servicios y 4 doctores con horarios y perfiles.
- Las notificaciones por email usan consola en desarrollo. Para SMTP, configura las variables en `settings.py`.
- El sistema está preparado para agregar carga de fotos reales y mejoras de agenda en tiempo real.

---

