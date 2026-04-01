from .models import Profesor, Curso

def global_context(request):
       # Obtener todos los profesores y cursos para el navbar
       all_professors = Profesor.objects.all()
       all_cursos = Curso.objects.all()
       return {
           'all_professors': all_professors,
           'all_cursos': all_cursos,
       }
       