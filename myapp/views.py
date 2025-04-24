# myapp/views.py
from django.shortcuts import render, redirect
from .models import (
    Profesor, DiaSemana, Asignacion, Curso, Materia, Apoderado, RangoNoDisponible,
    ProfesorHorario, Mensualidad, AnioEscolar, Alumno, Descuento
)
from datetime import time, datetime, timedelta
from django import forms
import logging
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from calendar import monthrange
import json
from decimal import Decimal
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.contrib import messages
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required



# Configuración del logger
logger = logging.getLogger(__name__)

# Formulario para Asignacion
class AsignacionForm(forms.Form):
    profesor = forms.ModelChoiceField(queryset=Profesor.objects.all(), label="Profesor")
    materia = forms.ModelChoiceField(queryset=Materia.objects.all(), label="Materia")
    curso = forms.ModelChoiceField(queryset=Curso.objects.all(), label="Curso")
    dia = forms.ModelChoiceField(queryset=DiaSemana.objects.none(), label="Día")
    hora_inicio = forms.CharField(max_length=5, label="Hora Inicio")
    hora_fin = forms.CharField(max_length=5, label="Hora Fin")
    selected_slots = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        available_days = kwargs.pop('available_days', DiaSemana.objects.none())
        super().__init__(*args, **kwargs)
        self.fields['dia'].queryset = available_days

# Funciones auxiliares
def time_to_minutes(t):
    return t.hour * 60 + t.minute

def merge_intervals(intervals):
    if not intervals:
        return []
    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    merged = [sorted_intervals[0]]
    for current in sorted_intervals[1:]:
        last = merged[-1]
        if current[0] <= last[1]:
            merged[-1] = (last[0], max(last[1], current[1]))
        else:
            merged.append(current)
    return merged

def calculate_available(total_start, total_end, assigned):
    available = []
    if not assigned:
        return [(total_start, total_end)]
    if total_start < assigned[0][0]:
        available.append((total_start, assigned[0][0]))
    for i in range(len(assigned)-1):
        current_end = assigned[i][1]
        next_start = assigned[i+1][0]
        if current_end < next_start:
            available.append((current_end, next_start))
    last_end = assigned[-1][1]
    if last_end < total_end:
        available.append((last_end, total_end))
    return available

def min_to_time(mins):
    hours, remainder = divmod(mins, 60)
    return time(hours, remainder)

def intersect_intervals(intervals1, intervals2):
    result = []
    i = j = 0
    while i < len(intervals1) and j < len(intervals2):
        start = max(intervals1[i][0], intervals2[j][0])
        end = min(intervals1[i][1], intervals2[j][1])
        if start < end:
            result.append((start, end))
        if intervals1[i][1] < intervals2[j][1]:
            i += 1
        else:
            j += 1
    return result

def get_common_context():
    all_professors = Profesor.objects.all()
    all_cursos = Curso.objects.all()
    logger.debug(f"Profesores cargados: {[p.id for p in all_professors]}")
    logger.debug(f"Cursos cargados: {[c.id for c in all_cursos]}")
    return {
        'all_professors': all_professors,
        'all_cursos': all_cursos,
    }

# Vistas
@login_required(login_url='/accounts/login/')
def index(request):
    context = get_common_context()
    return render(request, 'myapp/index.html', context)

@login_required(login_url='/accounts/login/')
def professor_schedule(request, professor_id):
    try:
        professor = Profesor.objects.get(id=professor_id)
    except Profesor.DoesNotExist:
        return render(request, 'myapp/404.html', status=404)

    days = DiaSemana.objects.all()
    schedule_data = {}
    
    total_start_time = time(8, 0)
    total_end_time = time(23, 0)
    
    intervals = []
    current_time = total_start_time
    while current_time <= total_end_time:
        intervals.append(current_time)
        current_time = (datetime.combine(datetime.today(), current_time) + timedelta(minutes=15)).time()
    
    for day in days:
        assignments = Asignacion.objects.filter(profesor=professor, dia=day)
        no_disponibles = RangoNoDisponible.objects.filter(dia=day)
        
        assigned_display = [
            (asig.hora_inicio, asig.hora_fin, f"{asig.materia.nombre} ({asig.curso.nombre})", time_to_minutes(asig.hora_fin) - time_to_minutes(asig.hora_inicio))
            for asig in assignments
        ]
        
        slots = []
        for i, slot_time in enumerate(intervals):
            assignment = False
            for start, end, _, _ in assigned_display:
                start_min = time_to_minutes(start)
                end_min = time_to_minutes(end)
                slot_min = time_to_minutes(slot_time)
                if start_min <= slot_min <= end_min:
                    assignment = True
                    break
            
            no_disponible = False
            for r in no_disponibles:
                start_min = time_to_minutes(r.hora_inicio)
                end_min = time_to_minutes(r.hora_fin)
                slot_min = time_to_minutes(slot_time)
                if start_min <= slot_min <= end_min:
                    no_disponible = True
                    break
            
            slots.append((slot_time, assignment, no_disponible))
        
        assigned_intervals_for_merging = [(time_to_minutes(asig.hora_inicio), time_to_minutes(asig.hora_fin)) for asig in assignments]
        no_disponible_intervals = [(time_to_minutes(r.hora_inicio), time_to_minutes(r.hora_fin)) for r in no_disponibles]
        total_start_min = time_to_minutes(total_start_time)
        total_end_min = time_to_minutes(total_end_time)
        all_blocked_intervals = merge_intervals(assigned_intervals_for_merging + no_disponible_intervals)
        available_intervals_minutes = calculate_available(total_start_min, total_end_min, all_blocked_intervals)
        available_display = [(min_to_time(start), min_to_time(end)) for start, end in available_intervals_minutes]
        
        schedule_data[day.nombre] = {
            'slots': slots,
            'assigned': assigned_display,
            'available': available_display,
        }
    
    context = get_common_context()
    context.update({
        'professor': professor,
        'schedule_data': schedule_data,
    })
    return render(request, 'myapp/schedule.html', context)

@login_required(login_url='/accounts/login/')
def curso_schedule(request, curso_id):
    try:
        curso = Curso.objects.get(id=curso_id)
    except Curso.DoesNotExist:
        return render(request, 'myapp/404.html', status=404)

    days = DiaSemana.objects.all()
    schedule_data = {}
    
    total_start_time = time(8, 0)
    total_end_time = time(23, 0)
    
    intervals = []
    current_time = total_start_time
    while current_time <= total_end_time:
        intervals.append(current_time)
        current_time = (datetime.combine(datetime.today(), current_time) + timedelta(minutes=15)).time()
    
    for day in days:
        assignments = Asignacion.objects.filter(curso=curso, dia=day)
        no_disponibles = RangoNoDisponible.objects.filter(dia=day)
        
        slots = []
        for i, slot_time in enumerate(intervals):
            prof_materia = None
            for asig in assignments:
                start_min = time_to_minutes(asig.hora_inicio)
                end_min = time_to_minutes(asig.hora_fin)
                slot_min = time_to_minutes(slot_time)
                if start_min <= slot_min <= end_min:
                    prof_materia = f"{asig.profesor.nombre}/{asig.materia.nombre}"
                    break
            
            no_disponible = False
            for r in no_disponibles:
                start_min = time_to_minutes(r.hora_inicio)
                end_min = time_to_minutes(r.hora_fin)
                slot_min = time_to_minutes(slot_time)
                if start_min <= slot_min <= end_min:
                    no_disponible = True
                    break
            
            slots.append((slot_time, prof_materia, no_disponible))
        
        schedule_data[day.nombre] = {
            'slots': slots,
        }
    
    context = get_common_context()
    context.update({
        'curso': curso,
        'schedule_data': schedule_data,
    })
    return render(request, 'myapp/cursos_scheduler.html', context)

@login_required(login_url='/accounts/login/')
def generate_curso_pdf(request, curso_id):
    try:
        curso = Curso.objects.get(id=curso_id)
    except Curso.DoesNotExist:
        return HttpResponse("Curso no encontrado.", status=404)

    days = DiaSemana.objects.all()
    schedule_data = {}
    
    total_start_time = time(8, 0)
    total_end_time = time(23, 0)
    
    intervals = []
    current_time = total_start_time
    while current_time <= total_end_time:
        intervals.append(current_time)
        current_time = (datetime.combine(datetime.today(), current_time) + timedelta(minutes=15)).time()
    
    for day in days:
        assignments = Asignacion.objects.filter(curso=curso, dia=day)
        no_disponibles = RangoNoDisponible.objects.filter(dia=day)
        prof_materia_slots = {}
        no_disponible_slots = [False] * len(intervals)
        for asig in assignments:
            key = f"{asig.profesor.nombre}/{asig.materia.nombre}"
            if key not in prof_materia_slots:
                prof_materia_slots[key] = [False] * len(intervals)
            start_min = time_to_minutes(asig.hora_inicio)
            end_min = time_to_minutes(asig.hora_fin)
            for i, slot_time in enumerate(intervals):
                slot_min = time_to_minutes(slot_time)
                if start_min <= slot_min <= end_min:
                    prof_materia_slots[key][i] = True
        for r in no_disponibles:
            start_min = time_to_minutes(r.hora_inicio)
            end_min = time_to_minutes(r.hora_fin)
            for i, slot_time in enumerate(intervals):
                slot_min = time_to_minutes(slot_time)
                if start_min <= slot_min <= end_min:
                    no_disponible_slots[i] = True
        
        schedule_data[day.nombre] = {
            'prof_materia_slots': prof_materia_slots,
            'intervals': intervals,
            'no_disponible_slots': no_disponible_slots,
        }
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="horario_curso_{curso.nombre}.pdf"'
    
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    
    p.setFont("Helvetica-Bold", 16)
    p.drawString(1 * inch, height - 1 * inch, f"Horario de {curso.nombre}")
    
    y = height - 1.5 * inch
    
    for day, data in schedule_data.items():
        p.setFont("Helvetica-Bold", 12)
        p.drawString(1 * inch, y, day)
        y -= 0.5 * inch
        
        p.setFont("Helvetica", 10)
        p.drawString(1 * inch, y, "Horario")
        p.drawString(3 * inch, y, "Profesor/Materia")
        y -= 0.3 * inch
        
        p.line(1 * inch, y, width - 1 * inch, y)
        y -= 0.2 * inch
        
        p.setFont("Helvetica", 9)
        for i in range(len(data['intervals'])):
            slot_time = data['intervals'][i]
            if y < 1 * inch:
                p.showPage()
                y = height - 1 * inch
                p.setFont("Helvetica", 9)
            
            p.drawString(1 * inch, y, slot_time.strftime('%H:%M'))
            
            text = ""
            for prof_materia, slots in data['prof_materia_slots'].items():
                if slots[i]:
                    text = prof_materia
                    break
            if data['no_disponible_slots'][i]:
                text = "No disponible"
            p.drawString(3 * inch, y, text)
            
            y -= 0.3 * inch
        
        y -= 0.5 * inch
    
    p.showPage()
    p.save()
    return response

@login_required(login_url='/accounts/login/')
def cargar_asignacion(request):
    total_start_time = time(8, 0)
    total_end_time = time(23, 0)

    all_intervals = []
    current_time = total_start_time
    while current_time <= total_end_time:
        all_intervals.append(current_time)
        current_time = (datetime.combine(datetime.today(), current_time) + timedelta(minutes=15)).time()

    profesor_id = request.POST.get('profesor', None) if request.method == 'POST' else None
    curso_id = request.POST.get('curso', None) if request.method == 'POST' else None
    dia_id = request.POST.get('dia', None) if request.method == 'POST' else None

    available_days = DiaSemana.objects.all()
    blocked_times = []
    assigned_slots = []
    available_slots = []
    error_message = None
    remaining_horas = None

    if dia_id:
        try:
            dia = DiaSemana.objects.get(id=dia_id)
            no_disponibles = RangoNoDisponible.objects.filter(dia=dia)
            for r in no_disponibles:
                current = r.hora_inicio
                while current < r.hora_fin:
                    blocked_times.append(current.strftime('%H:%M'))
                    current = (datetime.combine(datetime.today(), current) + timedelta(minutes=15)).time()
        except DiaSemana.DoesNotExist:
            error_message = "Día no encontrado."

    if profesor_id is not None:
        try:
            profesor = Profesor.objects.get(id=profesor_id)
            horarios = ProfesorHorario.objects.filter(profesor=profesor)
            available_days_ids = []
            for horario in horarios:
                dia = horario.dia
                limite_horas = horario.horas
                asignaciones = Asignacion.objects.filter(profesor=profesor, dia=dia)
                total_asignado = sum(
                    (time_to_minutes(asig.hora_fin) - time_to_minutes(asig.hora_inicio))
                    for asig in asignaciones
                )
                if total_asignado < limite_horas:
                    available_days_ids.append(dia.id)
            available_days = DiaSemana.objects.filter(id__in=available_days_ids)
        except Profesor.DoesNotExist:
            available_days = DiaSemana.objects.none()
            error_message = "Profesor no encontrado."

    if profesor_id is not None and curso_id is not None and dia_id is not None:
        try:
            profesor = Profesor.objects.get(id=profesor_id)
            curso = Curso.objects.get(id=curso_id)
            dia = DiaSemana.objects.get(id=dia_id)

            try:
                horario = ProfesorHorario.objects.get(profesor=profesor, dia=dia)
                limite_horas = horario.horas
            except ProfesorHorario.DoesNotExist:
                limite_horas = 0
                error_message = f"No se ha definido un límite de horas para {profesor.nombre} en {dia.nombre}."

            asignaciones = Asignacion.objects.filter(profesor=profesor, dia=dia)
            total_asignado = sum(
                (time_to_minutes(asig.hora_fin) - time_to_minutes(asig.hora_inicio))
                for asig in asignaciones
            )
            remaining_horas = max(0, limite_horas - total_asignado)

            if remaining_horas <= 0:
                error_message = f"No hay horas disponibles para {profesor.nombre} en {dia.nombre} (límite alcanzado)."
            else:
                profesor_assignments = Asignacion.objects.filter(profesor=profesor, dia=dia)
                profesor_assigned_intervals = [(time_to_minutes(asig.hora_inicio), time_to_minutes(asig.hora_fin)) for asig in profesor_assignments]
                curso_assignments = Asignacion.objects.filter(curso=curso, dia=dia).exclude(profesor=profesor)
                curso_assigned_intervals = [(time_to_minutes(asig.hora_inicio), time_to_minutes(asig.hora_fin)) for asig in curso_assignments]
                no_disponibles = RangoNoDisponible.objects.filter(dia=dia)
                no_disponible_intervals = [(time_to_minutes(r.hora_inicio), time_to_minutes(r.hora_fin)) for r in no_disponibles]

                profesor_merged_assigned = merge_intervals(profesor_assigned_intervals)
                curso_merged_assigned = merge_intervals(curso_assigned_intervals)
                no_disponible_merged = merge_intervals(no_disponible_intervals)

                total_start_min = time_to_minutes(total_start_time)
                total_end_min = time_to_minutes(total_end_time)
                profesor_available_intervals = calculate_available(total_start_min, total_end_min, profesor_merged_assigned)
                curso_available_intervals = calculate_available(total_start_min, total_end_min, curso_merged_assigned)
                no_disponible_available_intervals = calculate_available(total_start_min, total_end_min, no_disponible_merged)

                final_available_intervals = intersect_intervals(
                    intersect_intervals(profesor_available_intervals, curso_available_intervals),
                    no_disponible_available_intervals
                )

                for start_min, end_min in final_available_intervals:
                    current_min = start_min
                    while current_min < end_min:
                        available_slots.append(min_to_time(current_min).strftime('%H:%M'))
                        current_min += 15

                for asig in profesor_assignments:
                    current = asig.hora_inicio
                    while current < asig.hora_fin:
                        time_str = current.strftime('%H:%M')
                        assigned_slots.append({
                            'time': time_str,
                            'description': f"{asig.materia.nombre} ({asig.curso.nombre})"
                        })
                        current = (datetime.combine(datetime.today(), current) + timedelta(minutes=15)).time()
        except (Profesor.DoesNotExist, Curso.DoesNotExist, DiaSemana.DoesNotExist) as e:
            error_message = f"Datos no encontrados: {str(e)}"

    form = AsignacionForm(
        request.POST if request.method == 'POST' else None,
        available_days=available_days
    )

    if request.method == 'POST' and form.is_valid():
        selected_slots = form.cleaned_data.get('selected_slots')
        if selected_slots:
            slots = json.loads(selected_slots)
            if slots:
                start_time_str = slots[0]
                end_time_str = slots[-1]
                start_hour, start_minute = map(int, start_time_str.split(':'))
                end_hour, end_minute = map(int, end_time_str.split(':'))
                end_time_adjusted = (datetime.combine(datetime.today(), time(end_hour, end_minute)) + timedelta(minutes=15)).time()
                
                Asignacion.objects.create(
                    profesor=form.cleaned_data['profesor'],
                    materia=form.cleaned_data['materia'],
                    curso=form.cleaned_data['curso'],
                    dia=form.cleaned_data['dia'],
                    hora_inicio=time(start_hour, start_minute),
                    hora_fin=end_time_adjusted,
                    anio_escolar=form.cleaned_data['curso'].anio_escolar
                )
                messages.success(request, "Asignación creada con éxito.")
                return redirect('index')
            else:
                error_message = "No se seleccionaron slots."
        else:
            error_message = "No se seleccionaron slots."

    context = get_common_context()
    context.update({
        'form': form,
        'blocked_times': blocked_times,
        'assigned_slots': assigned_slots,
        'available_slots': available_slots,
        'error_message': error_message,
        'remaining_horas': remaining_horas,
    })
    return render(request, 'myapp/cargar_asignacion.html', context)

@login_required(login_url='/accounts/login/')
def get_schedule_data(request):
    profesor_id = request.GET.get('profesor_id')
    curso_id = request.GET.get('curso_id')
    dia_id = request.GET.get('dia_id')

    if not all([profesor_id, curso_id, dia_id]):
        return JsonResponse({'error': 'Faltan parámetros'}, status=400)

    try:
        profesor = Profesor.objects.get(id=profesor_id)
        curso = Curso.objects.get(id=curso_id)
        dia = DiaSemana.objects.get(id=dia_id)
    except (Profesor.DoesNotExist, Curso.DoesNotExist, DiaSemana.DoesNotExist):
        return JsonResponse({'error': 'Datos no encontrados'}, status=404)

    total_start_time = time(8, 0)
    total_end_time = time(23, 0)

    all_intervals = []
    current_time = total_start_time
    while current_time <= total_end_time:
        all_intervals.append(current_time)
        current_time = (datetime.combine(datetime.today(), current_time) + timedelta(minutes=15)).time()

    blocked_times = []
    assigned_slots = []
    available_slots = []
    remaining_horas = None

    no_disponibles = RangoNoDisponible.objects.filter(dia=dia)
    for r in no_disponibles:
        current = r.hora_inicio
        while current < r.hora_fin:
            blocked_times.append(current.strftime('%H:%M'))
            current = (datetime.combine(datetime.today(), current) + timedelta(minutes=15)).time()

    try:
        horario = ProfesorHorario.objects.get(profesor=profesor, dia=dia)
        limite_horas = horario.horas
    except ProfesorHorario.DoesNotExist:
        limite_horas = 0

    asignaciones = Asignacion.objects.filter(profesor=profesor, dia=dia)
    total_asignado = sum(
        (time_to_minutes(asig.hora_fin) - time_to_minutes(asig.hora_inicio))
        for asig in asignaciones
    )
    remaining_horas = max(0, limite_horas - total_asignado)

    if remaining_horas > 0:
        profesor_assignments = Asignacion.objects.filter(profesor=profesor, dia=dia)
        profesor_assigned_intervals = [(time_to_minutes(asig.hora_inicio), time_to_minutes(asig.hora_fin)) for asig in profesor_assignments]
        curso_assignments = Asignacion.objects.filter(curso=curso, dia=dia).exclude(profesor=profesor)
        curso_assigned_intervals = [(time_to_minutes(asig.hora_inicio), time_to_minutes(asig.hora_fin)) for asig in curso_assignments]
        no_disponible_intervals = [(time_to_minutes(r.hora_inicio), time_to_minutes(r.hora_fin)) for r in no_disponibles]

        profesor_merged_assigned = merge_intervals(profesor_assigned_intervals)
        curso_merged_assigned = merge_intervals(curso_assigned_intervals)
        no_disponible_merged = merge_intervals(no_disponible_intervals)

        total_start_min = time_to_minutes(total_start_time)
        total_end_min = time_to_minutes(total_end_time)
        profesor_available_intervals = calculate_available(total_start_min, total_end_min, profesor_merged_assigned)
        curso_available_intervals = calculate_available(total_start_min, total_end_min, curso_merged_assigned)
        no_disponible_available_intervals = calculate_available(total_start_min, total_end_min, no_disponible_merged)

        final_available_intervals = intersect_intervals(
            intersect_intervals(profesor_available_intervals, curso_available_intervals),
            no_disponible_available_intervals
        )

        for start_min, end_min in final_available_intervals:
            current_min = start_min
            while current_min < end_min:
                available_slots.append(min_to_time(current_min).strftime('%H:%M'))
                current_min += 15

        for asig in profesor_assignments:
            current = asig.hora_inicio
            while current < asig.hora_fin:
                time_str = current.strftime('%H:%M')
                assigned_slots.append({
                    'time': time_str,
                    'description': f"{asig.materia.nombre} ({asig.curso.nombre})"
                })
                current = (datetime.combine(datetime.today(), current) + timedelta(minutes=15)).time()

    return JsonResponse({
        'blocked_times': blocked_times,
        'assigned_slots': assigned_slots,
        'available_slots': available_slots,
        'remaining_horas': remaining_horas,
    })

@login_required(login_url='/accounts/login/')
def ingresos(request):
    apoderados = Apoderado.objects.all()
    apoderados_data = []
    today = timezone.now().date()

    for apoderado in apoderados:
        mensualidades = apoderado.mensualidades.all()
        total_pendiente = mensualidades.filter(estado='pendiente').aggregate(Sum('monto'))['monto__sum'] or Decimal('0')
        total_pagado = mensualidades.filter(estado='pagado').aggregate(Sum('monto'))['monto__sum'] or Decimal('0')
        total_atrasado = mensualidades.filter(estado='pendiente', fecha_vencimiento__lt=today).aggregate(Sum('monto'))['monto__sum'] or Decimal('0')

        apoderados_data.append({
            'apoderado': apoderado,
            'total_pendiente': total_pendiente,
            'total_atrasado': total_atrasado,
            'total_cancelado': total_pagado,
        })

    return render(request, 'myapp/ingresos.html', {'apoderados_data': apoderados_data})

@login_required(login_url='/accounts/login/')
def ingresos_details(request, apoderado_id):
    try:
        apoderado = Apoderado.objects.get(id=apoderado_id)
    except Apoderado.DoesNotExist:
        return JsonResponse({'error': 'Apoderado no encontrado'}, status=404)

    alumnos = apoderado.alumnos.all()
    mensualidades = apoderado.mensualidades.all()
    today = timezone.now().date()

    total_pendiente = mensualidades.filter(estado='pendiente').aggregate(Sum('monto'))['monto__sum'] or Decimal('0')
    total_pagado = mensualidades.filter(estado='pagado').aggregate(Sum('monto'))['monto__sum'] or Decimal('0')
    total_atrasado = mensualidades.filter(estado='pendiente', fecha_vencimiento__lt=today).aggregate(Sum('monto'))['monto__sum'] or Decimal('0')

    pie_data = {
        'labels': ['Pendiente', 'Atrasado', 'Pagado'],
        'values': [float(total_pendiente), float(total_atrasado), float(total_pagado)]
    }

    html = render_to_string('myapp/ingresos_details.html', {
        'apoderado': apoderado,
        'alumnos': alumnos,
        'mensualidades': mensualidades,
        'total_pendiente': total_pendiente,
        'total_atrasado': total_atrasado,
        'total_cancelado': total_pagado,
        'pie_data': pie_data,
    })

    return JsonResponse({
        'html': html,
        'pie_data': pie_data,
        'total_pendiente': float(total_pendiente),
        'total_atrasado': float(total_atrasado),
        'total_cancelado': float(total_pagado),
    })

@login_required(login_url='/accounts/login/')
@require_POST
def marcar_mensualidad_pagada(request):
    mensualidad_id = request.POST.get('mensualidad_id')
    metodo_pago = request.POST.get('metodo_pago')

    if not all([mensualidad_id, metodo_pago]):
        return JsonResponse({'success': False, 'error': 'Faltan parámetros'}, status=400)

    try:
        mensualidad = Mensualidad.objects.get(id=mensualidad_id)
    except Mensualidad.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Mensualidad no encontrada'}, status=404)

    if mensualidad.estado == 'pagado':
        return JsonResponse({'success': False, 'error': 'La mensualidad ya está pagada'}, status=400)

    mensualidad.estado = 'pagado'
    mensualidad.fecha_pago = timezone.now().date()
    mensualidad.metodo_pago = metodo_pago
    mensualidad.save()

    apoderado = mensualidad.apoderado
    mensualidades = apoderado.mensualidades.all()
    today = timezone.now().date()

    total_pendiente = mensualidades.filter(estado='pendiente').aggregate(Sum('monto'))['monto__sum'] or Decimal('0')
    total_pagado = mensualidades.filter(estado='pagado').aggregate(Sum('monto'))['monto__sum'] or Decimal('0')
    total_atrasado = mensualidades.filter(estado='pendiente', fecha_vencimiento__lt=today).aggregate(Sum('monto'))['monto__sum'] or Decimal('0')

    pie_data = {
        'labels': ['Pendiente', 'Atrasado', 'Pagado'],
        'values': [float(total_pendiente), float(total_atrasado), float(total_pagado)]
    }

    return JsonResponse({
        'success': True,
        'total_pendiente': float(total_pendiente),
        'total_atrasado': float(total_atrasado),
        'total_cancelado': float(total_pagado),
        'pie_data': pie_data,
    })

@login_required(login_url='/accounts/login/')
def reportes(request):
    mensualidades = Mensualidad.objects.all()
    today = timezone.now().date()

    ingresos_por_mes = mensualidades.filter(estado='pagado').annotate(
        mes=TruncMonth('fecha_pago')
    ).values('mes').annotate(
        total=Sum('monto')
    ).order_by('mes')

    morosidad_por_mes = mensualidades.filter(
        estado='pendiente',
        fecha_vencimiento__lt=today
    ).annotate(
        mes=TruncMonth('fecha_vencimiento')
    ).values('mes').annotate(
        total=Sum('monto')
    ).order_by('mes')

    return render(request, 'myapp/reportes.html', {
        'ingresos_por_mes': ingresos_por_mes,
        'morosidad_por_mes': morosidad_por_mes,
    })

@login_required(login_url='/accounts/login/')
def apoderados(request):
    anios_escolares = AnioEscolar.objects.all()
    return render(request, 'myapp/apoderados.html', {'anios_escolares': anios_escolares})

@login_required(login_url='/accounts/login/')
def apoderados_data(request):
    anio_escolar_id = request.GET.get('anio_escolar_id')
    if anio_escolar_id:
        apoderados = Apoderado.objects.filter(anio_escolar_id=anio_escolar_id)
    else:
        apoderados = Apoderado.objects.all()

    data = [
        {
            'apoderado_id': apoderado.id,  # Necesario para construir URLs en el frontend
            'nombre': apoderado.nombre,
            'apellidop': apoderado.apellidop,
            'apellidom': apoderado.apellidom,
            'email': apoderado.email,
            'telefono': apoderado.telefono if apoderado.telefono else '-',
            'rut': apoderado.rut,
            'arancel_anual': float(apoderado.arancel_anual),
            'meses_pago': apoderado.meses_pago,
            'cantidad_alumnos': apoderado.cantidad_alumnos,
            'modalidad_pago': apoderado.get_modalidad_pago_display(),
        }
        for apoderado in apoderados
    ]
    return JsonResponse({'data': data})

@login_required(login_url='/accounts/login/')
@require_POST
def apoderados_create(request):
    try:
        # Obtener los datos del formulario
        nombre = request.POST.get('nombre')
        apellidop = request.POST.get('apellidop')
        apellidom = request.POST.get('apellidom')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono', '')
        rut = request.POST.get('rut')
        arancel_anual = request.POST.get('arancel_anual')
        meses_pago = request.POST.get('meses_pago')
        cantidad_alumnos = request.POST.get('cantidad_alumnos')
        fecha_inicio = request.POST.get('fecha_inicio')
        anio_escolar_id = request.POST.get('anio_escolar')
        modalidad_pago = request.POST.get('modalidad_pago')

        # Validaciones básicas
        if not all([nombre, apellidop, apellidom, email, rut, arancel_anual, meses_pago, cantidad_alumnos, anio_escolar_id, modalidad_pago]):
            return JsonResponse({'success': False, 'error': 'Faltan campos obligatorios'}, status=400)

        # Validar y convertir datos
        try:
            arancel_anual = Decimal(arancel_anual)
            meses_pago = int(meses_pago)
            cantidad_alumnos = int(cantidad_alumnos)
            anio_escolar = AnioEscolar.objects.get(id=anio_escolar_id)
        except (ValueError, AnioEscolar.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Datos inválidos'}, status=400)

        # Validar fecha_inicio si está presente
        if fecha_inicio:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Formato de fecha inválido'}, status=400)
        else:
            fecha_inicio = None

        # Verificar unicidad de email y rut
        if Apoderado.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'error': 'El email ya está registrado'}, status=400)
        if Apoderado.objects.filter(rut=rut).exists():
            return JsonResponse({'success': False, 'error': 'El RUT ya está registrado'}, status=400)

        # Crear el apoderado y las mensualidades asociadas
        apoderado = Apoderado.objects.create(
            nombre=nombre,
            apellidop=apellidop,
            apellidom=apellidom,
            email=email,
            telefono=telefono,
            rut=rut,
            arancel_anual=arancel_anual,
            meses_pago=meses_pago,
            cantidad_alumnos=cantidad_alumnos,
            fecha_inicio=fecha_inicio,
            anio_escolar=anio_escolar,
            modalidad_pago=modalidad_pago
        )

        # Crear mensualidades
        monto_mensual = (arancel_anual * cantidad_alumnos) / meses_pago
        fecha_inicio = apoderado.fecha_inicio or datetime.today().date()
        for i in range(meses_pago):
            fecha_vencimiento = fecha_inicio + timedelta(days=30 * i)
            Mensualidad.objects.create(
                apoderado=apoderado,
                monto=monto_mensual,
                fecha_vencimiento=fecha_vencimiento,
                estado='pendiente',
            )

        # Retornar los datos del apoderado creado para añadir a la grilla
        return JsonResponse({
            'success': True,
            'apoderado': {
                'apoderado_id': apoderado.id,
                'nombre': apoderado.nombre,
                'apellidop': apoderado.apellidop,
                'apellidom': apoderado.apellidom,
                'email': apoderado.email,
                'telefono': apoderado.telefono if apoderado.telefono else '-',
                'rut': apoderado.rut,
                'arancel_anual': float(apoderado.arancel_anual),
                'meses_pago': apoderado.meses_pago,
                'cantidad_alumnos': apoderado.cantidad_alumnos,
                'modalidad_pago': apoderado.get_modalidad_pago_display(),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required(login_url='/accounts/login/')
def alumnos(request, apoderado_id):
    try:
        apoderado = Apoderado.objects.get(id=apoderado_id)
    except Apoderado.DoesNotExist:
        return render(request, 'myapp/404.html', status=404)

    anios_escolares = AnioEscolar.objects.all()
    return render(request, 'myapp/alumnos.html', {
        'apoderado': apoderado,
        'anios_escolares': anios_escolares,
    })

@login_required(login_url='/accounts/login/')
def alumnos_data(request, apoderado_id):
    try:
        apoderado = Apoderado.objects.get(id=apoderado_id)
    except Apoderado.DoesNotExist:
        return JsonResponse({'data': []})

    alumnos = apoderado.alumnos.all()
    data = [
        {
            'nombre': alumno.nombre,
            'apellidop': alumno.apellidop,
            'apellidom': alumno.apellidom,
            'email': alumno.email if alumno.email else '-',
            'fecha_nacimiento': alumno.fecha_nacimiento.strftime('%Y-%m-%d'),
            'sexo': alumno.get_sexo_display(),
            'curso': alumno.curso.nombre if alumno.curso else '-',
            'anio_escolar': str(alumno.anio_escolar.anio),  # Ajustado
        }
        for alumno in alumnos
    ]
    return JsonResponse({'data': data})

@login_required(login_url='/accounts/login/')
def get_cursos_por_anio(request):
    anio_escolar_id = request.GET.get('anio_escolar_id')
    if not anio_escolar_id:
        return JsonResponse({'cursos': []})

    try:
        anio_escolar = AnioEscolar.objects.get(id=anio_escolar_id)
        cursos = Curso.objects.filter(anio_escolar=anio_escolar)
        cursos_data = [{'id': curso.id, 'nombre': curso.nombre} for curso in cursos]
        return JsonResponse({'cursos': cursos_data})
    except AnioEscolar.DoesNotExist:
        return JsonResponse({'cursos': []})

@login_required(login_url='/accounts/login/')
@require_POST
def alumnos_create(request, apoderado_id):
    try:
        apoderado = Apoderado.objects.get(id=apoderado_id)
    except Apoderado.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Apoderado no encontrado'}, status=404)

    try:
        nombre = request.POST.get('nombre')
        apellidop = request.POST.get('apellidop')
        apellidom = request.POST.get('apellidom')
        email = request.POST.get('email', '')
        fecha_nacimiento = request.POST.get('fecha_nacimiento')
        sexo = request.POST.get('sexo')
        curso_id = request.POST.get('curso')
        anio_escolar_id = request.POST.get('anio_escolar')

        if not all([nombre, apellidop, apellidom, fecha_nacimiento, sexo, curso_id, anio_escolar_id]):
            return JsonResponse({'success': False, 'error': 'Faltan campos obligatorios'}, status=400)

        fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
        curso = Curso.objects.get(id=curso_id)
        anio_escolar = AnioEscolar.objects.get(id=anio_escolar_id)
        

        if email and Alumno.objects.filter(email=email).exclude(apoderado=apoderado).exists():
            return JsonResponse({'success': False, 'error': 'El email ya está registrado'}, status=400)

        alumno = Alumno.objects.create(
            nombre=nombre,
            apellidop=apellidop,
            apellidom=apellidom,
            email=email if email else None,
            fecha_nacimiento=fecha_nacimiento,
            sexo=sexo,
            apoderado=apoderado,
            curso=curso,
            anio_escolar=anio_escolar,
        )

        return JsonResponse({
            'success': True,
            'alumno': {
                'nombre': alumno.nombre,
                'apellidop': alumno.apellidop,
                'apellidom': alumno.apellidom,
                'email': alumno.email if alumno.email else '-',
                'fecha_nacimiento': alumno.fecha_nacimiento.strftime('%Y-%m-%d'),
                'sexo': alumno.get_sexo_display(),
                'curso': alumno.curso.nombre if alumno.curso else '-',
                'anio_escolar': str(alumno.anio_escolar.anio),  # Ajustado
            }
        })
    except (ValueError, Curso.DoesNotExist, AnioEscolar.DoesNotExist) as e:
        return JsonResponse({'success': False, 'error': 'Datos inválidos: ' + str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    
@login_required(login_url='/accounts/login/')
def reporte_alumnos_por_anio_curso(request):
    # Esta vista solo renderiza el template
    return render(request, 'myapp/reporte_alumnos.html')

@login_required(login_url='/accounts/login/')
def reporte_alumnos_por_anio_curso_data(request):
    # Esta vista devuelve el JSON con los datos
    anios_escolares = AnioEscolar.objects.all()
    data = []

    for anio in anios_escolares:
        cursos = Curso.objects.filter(anio_escolar=anio)
        cursos_data = []

        for curso in cursos:
            alumnos = Alumno.objects.filter(curso=curso, anio_escolar=anio)
            alumnos_data = []

            for alumno in alumnos:
                apoderado = alumno.apoderado
                alumnos_data.append({
                    'nombre_alumno': alumno.nombre,
                    'apellidop_alumno': alumno.apellidop,
                    'apellidom_alumno': alumno.apellidom,
                    'email_alumno': alumno.email if alumno.email else '-',
                    'fecha_nacimiento': alumno.fecha_nacimiento.strftime('%Y-%m-%d'),
                    'sexo': alumno.get_sexo_display(),
                    'nombre_apoderado': apoderado.nombre,
                    'apellidop_apoderado': apoderado.apellidop,
                    'apellidom_apoderado': apoderado.apellidom,
                    'email_apoderado': apoderado.email if apoderado.email else '-',
                    'telefono_apoderado': apoderado.telefono if apoderado.telefono else '-',
                })

            cursos_data.append({
                'curso_nombre': curso.nombre,
                'alumnos': alumnos_data,
            })

        data.append({
            'anio': str(anio.anio),
            'cursos': cursos_data,
        })

    return JsonResponse({'data': data})

@login_required(login_url='/accounts/login/')
@require_POST
def aplicar_descuento(request):
    try:
        apoderado_id = request.POST.get('apoderado_id')
        descripcion = request.POST.get('descripcion')
        porcentaje = request.POST.get('porcentaje')
        mes_inicio = int(request.POST.get('mes_inicio'))

        if not all([apoderado_id, descripcion, porcentaje, mes_inicio]):
            return JsonResponse({'success': False, 'error': 'Faltan campos obligatorios'}, status=400)

        apoderado = Apoderado.objects.get(id=apoderado_id)
        porcentaje = Decimal(porcentaje)

        # Validar el mes de inicio
        if mes_inicio < 1 or mes_inicio > apoderado.meses_pago:
            return JsonResponse({'success': False, 'error': f'El mes de inicio debe estar entre 1 y {apoderado.meses_pago}'}, status=400)

        # Crear el descuento
        descuento = Descuento.objects.create(
            apoderado=apoderado,
            descripcion=descripcion,
            porcentaje=porcentaje,
            activo=True,
            anio_escolar=apoderado.anio_escolar
        )

        # Actualizar las mensualidades a partir del mes especificado
        mensualidades = Mensualidad.objects.filter(apoderado=apoderado, numero__gte=mes_inicio)
        for mensualidad in mensualidades:
            # Recalcular el monto con el nuevo descuento
            descuentos = apoderado.descuentos.filter(activo=True)
            total_descuento = sum(d.porcentaje for d in descuentos)
            factor_descuento = Decimal('1') - (total_descuento / Decimal('100'))
            monto_final = mensualidad.monto_inicial * factor_descuento
            descuentos_aplicados = ", ".join(f"{d.descripcion} ({d.porcentaje}%)" for d in descuentos) or "Ninguno"
            mensualidad.monto = monto_final
            mensualidad.descuentos_aplicados = descuentos_aplicados
            mensualidad.save()

        return JsonResponse({'success': True})
    except Apoderado.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Apoderado no encontrado'}, status=404)
    except (ValueError, TypeError) as e:
        return JsonResponse({'success': False, 'error': 'Datos inválidos: ' + str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)