# myproject/urls.py
from django.urls import path, include
from myapp import views
from django.views.generic.base import RedirectView

urlpatterns = [
    path('', views.index, name='index'),
    path('myapp/', RedirectView.as_view(url='/myapp/ingresos/', permanent=False), name='myapp_index'),
    path('myapp/schedule/<int:professor_id>/', views.professor_schedule, name='professor_schedule'),
    path('myapp/cursos/<int:curso_id>/', views.curso_schedule, name='curso_schedule'),
    path('myapp/cursos/pdf/<int:curso_id>/', views.generate_curso_pdf, name='generate_curso_pdf'),
    path('myapp/cargar_asignacion/', views.cargar_asignacion, name='cargar_asignacion'),
    path('myapp/get_schedule_data/', views.get_schedule_data, name='get_schedule_data'),
    path('myapp/ingresos/', views.ingresos, name='ingresos'),
    path('myapp/ingresos_details/<int:apoderado_id>/', views.ingresos_details, name='ingresos_details'),
    path('myapp/marcar_mensualidad_pagada/', views.marcar_mensualidad_pagada, name='marcar_mensualidad_pagada'),
    path('myapp/reportes/', views.reportes, name='reportes'),
    path('myapp/apoderados/', views.apoderados, name='apoderados'),
    path('myapp/apoderados_data/', views.apoderados_data, name='apoderados_data'),
    path('myapp/apoderados_create/', views.apoderados_create, name='apoderados_create'),
    path('myapp/apoderados/<int:apoderado_id>/alumnos/', views.alumnos, name='alumnos'),
    path('myapp/apoderados/<int:apoderado_id>/alumnos_data/', views.alumnos_data, name='alumnos_data'),
    path('myapp/apoderados/<int:apoderado_id>/alumnos_create/', views.alumnos_create, name='alumnos_create'),
    path('myapp/get_cursos_por_anio/', views.get_cursos_por_anio, name='get_cursos_por_anio'),
    path('accounts/', include('allauth.urls')),
    path('reporte_alumnos_por_anio_curso/', views.reporte_alumnos_por_anio_curso, name='reporte_alumnos_por_anio_curso'),
    path('reporte_alumnos_por_anio_curso_data/', views.reporte_alumnos_por_anio_curso_data, name='reporte_alumnos_por_anio_curso_data'),
]


