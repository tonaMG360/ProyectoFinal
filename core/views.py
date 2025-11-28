from django.contrib.auth.decorators import login_required
@login_required
def citas_pendientes(request):
    """Vista para que el paciente vea solo sus citas en estado PENDIENTE."""
    user = request.user
    try:
        paciente = user.paciente
    except Exception:
        paciente = None
    if paciente:
        citas = paciente.citas.filter(estado='PENDING')
    else:
        citas = []
    return render(request, 'core/citas_pendientes.html', {'citas': citas})
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .models import Servicio, Doctor, Paciente, Cita
from .forms import PatientRegistrationForm, CitaForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

# Create your views here.

def inicio(request):
    return render(request, 'core/inicio.html')

def productos(request):
    servicios = Servicio.objects.all()
    return render(request, 'core/productos.html', {'servicios': servicios})

def nosotros(request):
    doctores = Doctor.objects.all()
    return render(request, 'core/nosotros.html', {'doctores': doctores})


def doctores(request):
    """List doctors with optional filtering by 'especialidad' (GET param).

    This listing is public and each doctor card includes a "Reservar" button that
    links to the create appointment flow pre-filling the selected doctor.
    """
    especialidad = request.GET.get('especialidad')
    qs = Doctor.objects.all()
    if especialidad:
        qs = qs.filter(especialidad__icontains=especialidad)

    # collect distinct specialties for the filter dropdown
    especialidades = Doctor.objects.order_by('especialidad').values_list('especialidad', flat=True).distinct()
    return render(request, 'core/doctores.html', {'doctores': qs, 'especialidades': especialidades, 'selected': especialidad})


def doctor_detail(request, pk):
    """Show a doctor profile detail page (public).

    The page includes the doctor's bio, photo (placeholder URL), schedule and a 'Reservar' button
    that leads to the appointment creation form prefilled with the doctor id.
    """
    d = get_object_or_404(Doctor, pk=pk)
    return render(request, 'core/doctor_detail.html', {'doctor': d})

def pacientes(request):
    pacientes = Paciente.objects.all()
    return render(request, 'core/login_pacientes.html', {'login_pacientes': pacientes})


def register_paciente(request):
    """Simple registration view for patients using Django's User model and PatientRegistrationForm.

    After successful registration it creates a Paciente model entry (minimal) and logs the user in.
    """
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create a related Paciente record (or link to an existing one) to associate profile data with the new User.
            nombre = (user.get_full_name() or user.username).strip()
            paciente, created = Paciente.objects.get_or_create(nombre=nombre, defaults={'edad': 0, 'historial_medico': ''})
            paciente.user = user
            paciente.save()
            # Log the user in
            login(request, user)
            return redirect('login_pacientes')
    else:
        form = PatientRegistrationForm()

    return render(request, 'core/registro_paciente.html', {'form': form})


def crear_cita(request):
    """Create a new Cita for the logged-in paciente. If the user's Paciente does not exist yet,
    we create a minimal one and associate it. Supports preselecting a servicio via GET param 'servicio_id'.
    """
    # If user is not authenticated, add a helpful message and redirect to login (preserve next)
    user = request.user
    if not user.is_authenticated:
        # Add a friendly message explaining why they're redirected
        messages.info(request, 'Necesitas iniciar sesión para agendar una cita.')
        # preserve full path (including querystring) so user returns to the slot they requested
        from django.conf import settings
        from urllib.parse import quote
        next_url = quote(request.get_full_path())
        return redirect(f"{settings.LOGIN_URL}?next={next_url}")
    # Ensure paciente profile exists
    try:
        paciente = user.paciente
    except Exception:
        # create minimal Paciente and link
        nombre = (user.get_full_name() or user.username).strip()
        paciente = Paciente.objects.create(nombre=nombre, edad=0, historial_medico='', user=user)

    servicio_id = request.GET.get('servicio_id')
    servicio_instance = None
    if servicio_id:
        from .models import Servicio
        servicio_instance = get_object_or_404(Servicio, pk=servicio_id)

    if request.method == 'POST':
        form = CitaForm(request.POST, paciente=paciente)
        if form.is_valid():
            cita = form.save(commit=False, paciente=paciente)
            # if no doctor selected, try to auto-assign an available doctor for that slot
            if not cita.doctor:
                # compute end time using cita.duracion or servicio.duracion
                import datetime as _dt
                dur = cita.duracion or (cita.servicio.duracion if cita.servicio else 30)
                start_dt = cita.fecha_hora
                end_dt = start_dt + _dt.timedelta(minutes=int(dur))
                # find doctor available (availability window and no overlapping appointments)
                from .models import Doctor
                candidates = Doctor.objects.all()
                chosen = None
                for d in candidates:
                    if d.disponible_desde and d.disponible_hasta:
                        if not (d.disponible_desde <= start_dt.time() <= d.disponible_hasta and d.disponible_desde <= end_dt.time() <= d.disponible_hasta):
                            continue
                    # check overlap
                    if Cita.objects.filter(doctor=d, fecha_hora__lt=end_dt).exclude(pk=cita.pk if cita.pk else None):
                        # ensure none of them end after start
                        conflict = False
                        for ex in Cita.objects.filter(doctor=d, fecha_hora__lt=end_dt):
                            if ex.end_time > start_dt:
                                conflict = True
                                break
                        if conflict:
                            continue
                    chosen = d
                    break
                if chosen:
                    cita.doctor = chosen
            # paciente is assigned inside form.save if provided; we ensure paciente assigned
            if not cita.paciente:
                cita.paciente = paciente
            cita.save()
            # send confirmation email to patient (if email is available)
            # send HTML + plain-text confirmation email to patient (fail silently in dev)
            try:
                if request.user.email:
                    ctx = {
                        'paciente_name': request.user.get_full_name() or request.user.username,
                        'servicio': cita.servicio.titulo,
                        'fecha_hora': cita.fecha_hora,
                        'duracion': cita.duracion or cita.servicio.duracion,
                        'doctor': cita.doctor.nombre if cita.doctor else 'Pendiente',
                        'notas': cita.notas or 'N/A'
                    }
                    subject = f"Cita reservada: {cita.servicio.titulo}"
                    text_body = render_to_string('core/emails/cita_created.txt', ctx) if False else f"Tu cita para {cita.servicio.titulo} ha sido creada: {cita.fecha_hora}"
                    html_body = render_to_string('core/emails/cita_created.html', ctx)
                    msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [request.user.email])
                    msg.attach_alternative(html_body, 'text/html')
                    msg.send(fail_silently=True)
            except Exception:
                pass
            messages.success(request, 'Cita reservada correctamente.')
            return redirect('mis_citas')
    else:
        initial = {}
        if servicio_instance:
            initial['servicio'] = servicio_instance
        # allow pre-filling date/time from GET for UX (e.g. selecting a slot link)
        fecha_q = request.GET.get('fecha')
        hora_q = request.GET.get('hora')
        if fecha_q:
            initial['fecha'] = fecha_q
        if hora_q:
            initial['hora'] = hora_q
        if request.GET.get('doctor'):
            try:
                initial['doctor'] = int(request.GET.get('doctor'))
            except Exception:
                pass
        if request.GET.get('duracion'):
            try:
                initial['duracion'] = int(request.GET.get('duracion'))
            except Exception:
                pass
        form = CitaForm(initial=initial, paciente=paciente)

    # compute available slots for a selected date (optional) to help UX
    available_slots = []
    fecha_str = request.GET.get('fecha')
    if fecha_str and servicio_instance:
        import datetime as _dt
        from django.utils import timezone
        try:
            fecha_date = _dt.datetime.strptime(fecha_str, '%Y-%m-%d').date()
            # duration to use (service default unless user picks duration via GET)
            dur = int(request.GET.get('duracion') or servicio_instance.duracion or 30)

            # build time window to search: use doctor(s) availability if doctor selected in GET
            doctor_id = request.GET.get('doctor')
            doctors = []
            if doctor_id:
                from .models import Doctor
                try:
                    doctors = [Doctor.objects.get(pk=int(doctor_id))]
                except Exception:
                    doctors = list(Doctor.objects.all())
            else:
                from .models import Doctor
                doctors = list(Doctor.objects.all())

            # default search between 09:00 and 18:00 if no doctor availability defined
            start_time = _dt.time(9, 0)
            end_time = _dt.time(18, 0)

            for d in doctors:
                s = d.disponible_desde or start_time
                e = d.disponible_hasta or end_time
                # iterate slot by 30 minutes
                slot_dt = _dt.datetime.combine(fecha_date, s)
                end_day_dt = _dt.datetime.combine(fecha_date, e)
                while slot_dt + _dt.timedelta(minutes=dur) <= end_day_dt:
                    slot_end = slot_dt + _dt.timedelta(minutes=dur)
                    # check overlapping appointments for the doctor
                    conflicts = Cita.objects.filter(doctor=d, fecha_hora__lt=slot_end)
                    conflict_found = False
                    for ex in conflicts:
                        if ex.end_time > slot_dt:
                            conflict_found = True
                            break
                    if not conflict_found:
                        # add slot in ISO time format
                        available_slots.append({'doctor_id': d.id, 'doctor_name': d.nombre, 'time': slot_dt.time().strftime('%H:%M')})
                    slot_dt += _dt.timedelta(minutes=30)
        except Exception:
            available_slots = []

    return render(request, 'core/crear_cita.html', {'form': form, 'servicio': servicio_instance, 'available_slots': available_slots})


@login_required
def editar_cita(request, pk):
    """Edit a Cita belonging to the logged-in paciente."""
    cita = get_object_or_404(Cita, pk=pk, paciente__user=request.user)
    paciente = cita.paciente

    if request.method == 'POST':
        form = CitaForm(request.POST, instance=cita, paciente=paciente)
        if form.is_valid():
            cita = form.save(commit=False, paciente=paciente)
            if not cita.paciente:
                cita.paciente = paciente
            cita.save()
            # notify
            try:
                if request.user.email:
                    ctx = {
                        'paciente_name': request.user.get_full_name() or request.user.username,
                        'servicio': cita.servicio.titulo,
                        'fecha_hora': cita.fecha_hora,
                        'duracion': cita.duracion or cita.servicio.duracion,
                        'doctor': cita.doctor.nombre if cita.doctor else 'Pendiente',
                        'notas': cita.notas or 'N/A'
                    }
                    subject = f"Cita actualizada: {cita.servicio.titulo}"
                    text_body = f"Tu cita ha sido actualizada: {cita.fecha_hora}"
                    html_body = render_to_string('core/emails/cita_updated.html', ctx)
                    msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [request.user.email])
                    msg.attach_alternative(html_body, 'text/html')
                    msg.send(fail_silently=True)
            except Exception:
                pass
            messages.success(request, 'Cita actualizada correctamente.')
            return redirect('mis_citas')
    else:
        initial = {'fecha': cita.fecha_hora.date(), 'hora': cita.fecha_hora.time(), 'servicio': cita.servicio}
        form = CitaForm(instance=cita, initial=initial, paciente=paciente)

    return render(request, 'core/crear_cita.html', {'form': form, 'servicio': cita.servicio, 'edit_mode': True, 'cita': cita})


@login_required
def cancelar_cita(request, pk):
    """Cancel a Cita owned by the logged in user. Expects POST."""
    cita = get_object_or_404(Cita, pk=pk, paciente__user=request.user)
    if request.method == 'POST':
        cita.estado = 'CANCELLED'
        cita.save()
        # notify
        try:
            if request.user.email:
                ctx = {'paciente_name': request.user.get_full_name() or request.user.username, 'servicio': cita.servicio.titulo, 'fecha_hora': cita.fecha_hora}
                subject = f"Cita cancelada: {cita.servicio.titulo}"
                text_body = f"Tu cita del {cita.fecha_hora} ha sido cancelada."
                html_body = render_to_string('core/emails/cita_cancelled.html', ctx)
                msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [request.user.email])
                msg.attach_alternative(html_body, 'text/html')
                msg.send(fail_silently=True)
        except Exception:
            pass
        messages.success(request, 'Cita cancelada correctamente.')
        return redirect('mis_citas')
    # If GET, show confirmation page
    return render(request, 'core/cancelar_cita_confirm.html', {'cita': cita})


@login_required
def mis_citas(request):
    user = request.user
    try:
        paciente = user.paciente
    except Exception:
        paciente = None
    if paciente:
        citas = paciente.citas.all()
    else:
        citas = []
    return render(request, 'core/mis_citas.html', {'citas': citas})