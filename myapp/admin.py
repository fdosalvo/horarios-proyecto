# myapp/admin.py
from django.contrib import admin
from .models import (
    Profesor, Curso, DiaSemana, Asignacion, RangoNoDisponible, ProfesorHorario,
    Apoderado, Mensualidad, AnioEscolar, Alumno, Materia, Descuento
)

class AlumnoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellidop', 'apellidom', 'email', 'fecha_nacimiento', 'sexo', 'apoderado', 'curso', 'anio_escolar')
    list_filter = ('anio_escolar', 'curso', 'sexo')
    search_fields = ('nombre', 'apellidop', 'apellidom', 'email')

class ApoderadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellidop', 'apellidom', 'email', 'telefono', 'rut', 'anio_escolar', 'modalidad_pago')
    list_filter = ('anio_escolar', 'modalidad_pago')
    search_fields = ('nombre', 'apellidop', 'apellidom', 'email', 'rut')

class MensualidadAdmin(admin.ModelAdmin):
    list_display = ('apoderado', 'monto', 'fecha_vencimiento', 'estado', 'fecha_pago')
    list_filter = ('estado', 'fecha_vencimiento')
    search_fields = ('apoderado__nombre', 'apoderado__apellidop', 'apoderado__apellidom')

class AsignacionAdmin(admin.ModelAdmin):
    list_display = ('profesor', 'curso', 'dia', 'materia', 'hora_inicio', 'hora_fin')
    list_filter = ('dia', 'profesor', 'curso')
    search_fields = ('profesor__nombre', 'curso__nombre', 'materia__nombre')

class ProfesorHorarioAdmin(admin.ModelAdmin):
    list_display = ('profesor', 'dia', 'horas')
    list_filter = ('dia',)
    search_fields = ('profesor__nombre',)

admin.site.register(Profesor)
admin.site.register(Curso)
admin.site.register(DiaSemana)
admin.site.register(Asignacion, AsignacionAdmin)
admin.site.register(RangoNoDisponible)
admin.site.register(ProfesorHorario, ProfesorHorarioAdmin)
admin.site.register(Apoderado, ApoderadoAdmin)
admin.site.register(Mensualidad, MensualidadAdmin)
admin.site.register(AnioEscolar)
admin.site.register(Alumno, AlumnoAdmin)
admin.site.register(Materia)
admin.site.register(Descuento)
