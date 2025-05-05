from rest_framework import serializers
from .models import Apoderado, Alumno, Mensualidad

class MensualidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mensualidad
        fields = ['id', 'numero', 'monto', 'estado', 'fecha_vencimiento', 'fecha_pago', 'metodo_pago', 'descuentos_aplicados']

class AlumnoSerializer(serializers.ModelSerializer):
    mensualidades = MensualidadSerializer(many=True, read_only=True, source='apoderado.mensualidades')

    class Meta:
        model = Alumno
        fields = ['id', 'nombre', 'apellidop', 'apellidom', 'email', 'fecha_nacimiento', 'sexo', 'curso', 'mensualidades']

class ApoderadoSerializer(serializers.ModelSerializer):
    alumnos = AlumnoSerializer(many=True, read_only=True)

    class Meta:
        model = Apoderado
        fields = ['id', 'nombre', 'apellidop', 'apellidom', 'email', 'telefono', 'rut', 'arancel_anual', 'meses_pago', 'cantidad_alumnos', 'modalidad_pago', 'alumnos']