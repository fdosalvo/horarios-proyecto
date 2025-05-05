from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User

class AnioEscolar(models.Model):
    anio = models.IntegerField(unique=True, verbose_name="Año Escolar")
    descripcion = models.CharField(max_length=200, blank=True, verbose_name="Descripción")

    def __str__(self):
        return str(self.anio)

    class Meta:
        verbose_name = "Año Escolar"
        verbose_name_plural = "Años Escolares"

class Curso(models.Model):
    nombre = models.CharField(max_length=100)
    anio_escolar = models.ForeignKey(AnioEscolar, on_delete=models.CASCADE, related_name='cursos', null=True, blank=True)

    def __str__(self):
        return self.nombre

class Profesor(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class ProfesorHorario(models.Model):
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, related_name='horarios')
    dia = models.ForeignKey('DiaSemana', on_delete=models.CASCADE, related_name='horarios_profesores')
    horas = models.PositiveIntegerField(verbose_name="Horas (en minutos)", help_text="Límite de horas diarias en minutos (por ejemplo, 240 para 4 horas)")

    def __str__(self):
        return f"{self.profesor.nombre} - {self.dia.nombre}: {self.horas // 60}h {self.horas % 60}m"

    class Meta:
        verbose_name = "Horario de Profesor"
        verbose_name_plural = "Horarios de Profesores"
        unique_together = ['profesor', 'dia']

class Materia(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class DiaSemana(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre

class RangoNoDisponible(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del Rango")
    dia = models.ForeignKey(DiaSemana, on_delete=models.CASCADE, related_name='rangos_no_disponibles')
    hora_inicio = models.TimeField(verbose_name="Hora de Inicio")
    hora_fin = models.TimeField(verbose_name="Hora de Fin")

    def __str__(self):
        return f"{self.nombre} ({self.dia.nombre}: {self.hora_inicio} - {self.hora_fin})"

    class Meta:
        verbose_name = "Rango No Disponible"
        verbose_name_plural = "Rangos No Disponibles"

class Asignacion(models.Model):
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    dia = models.ForeignKey(DiaSemana, on_delete=models.CASCADE)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    anio_escolar = models.ForeignKey(AnioEscolar, on_delete=models.CASCADE, related_name='asignaciones', null=True, blank=True)

    def __str__(self):
        return f"{self.materia} - {self.curso} ({self.dia})"

class Apoderado(models.Model):
    MODALIDAD_PAGO_CHOICES = (
        ('efectivo', 'Efectivo'),
        ('cheque', 'Cheque'),
        ('tarjeta', 'Tarjeta'),
        ('letra', 'Letra'),
    )
    nombre = models.CharField(max_length=100)
    apellidop = models.CharField(max_length=100, verbose_name="Apellido Paterno")
    apellidom = models.CharField(max_length=100, verbose_name="Apellido Materno")
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    rut = models.CharField(max_length=12, unique=True)
    arancel_anual = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    meses_pago = models.PositiveIntegerField(default=10, validators=[MinValueValidator(1), MaxValueValidator(10)])
    cantidad_alumnos = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], verbose_name="Cantidad de Alumnos")
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio de Mensualidades", null=True, blank=True)
    anio_escolar = models.ForeignKey(AnioEscolar, on_delete=models.CASCADE, related_name='apoderados', null=True, blank=True)
    modalidad_pago = models.CharField(max_length=20, choices=MODALIDAD_PAGO_CHOICES, blank=False, verbose_name="Modalidad de Pago")

    def __str__(self):
        return f"{self.nombre} {self.apellidop} {self.apellidom}"

    def calcular_mensualidades(self):
        self.mensualidades.all().delete()
        monto_base = (self.arancel_anual * self.cantidad_alumnos) / self.meses_pago
        descuentos = self.descuentos.filter(activo=True)
        total_descuento = sum(descuento.porcentaje for descuento in descuentos)
        factor_descuento = Decimal('1') - (total_descuento / Decimal('100'))
        monto_final = monto_base * factor_descuento
        descuentos_aplicados = ", ".join(f"{d.descripcion} ({d.porcentaje}%)" for d in descuentos) or "Ninguno"
        current = self.fecha_inicio
        for i in range(1, self.meses_pago + 1):
            Mensualidad.objects.create(
                apoderado=self,
                numero=i,
                monto_inicial=monto_base,
                monto=monto_final,
                descuentos_aplicados=descuentos_aplicados,
                fecha_vencimiento=current,
                estado='pendiente',
                anio_escolar=self.anio_escolar
            )
            next_month = current.month + 1 if current.month < 12 else 1
            next_year = current.year if current.month < 12 else current.year + 1
            try:
                current = current.replace(year=next_year, month=next_month)
            except ValueError:
                current = current.replace(year=next_year, month=next_month, day=1)

class Alumno(models.Model):
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]
    nombre = models.CharField(max_length=100)
    apellidop = models.CharField(max_length=100)
    apellidom = models.CharField(max_length=100)
    email = models.EmailField(unique=True, blank=True, null=True)
    fecha_nacimiento = models.DateField()
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES)
    apoderado = models.ForeignKey(Apoderado, on_delete=models.CASCADE, related_name='alumnos')
    curso = models.ForeignKey(Curso, on_delete=models.SET_NULL, null=True)
    anio_escolar = models.ForeignKey(AnioEscolar, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombre} {self.apellidop} {self.apellidom}"

class Descuento(models.Model):
    apoderado = models.ForeignKey(Apoderado, on_delete=models.CASCADE, related_name='descuentos')
    descripcion = models.CharField(max_length=200)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    activo = models.BooleanField(default=True)
    anio_escolar = models.ForeignKey(AnioEscolar, on_delete=models.CASCADE, related_name='descuentos', null=True, blank=True)

    def __str__(self):
        return f"{self.descripcion} ({self.porcentaje}%)"

class Mensualidad(models.Model):
    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('atrasado', 'Atrasado'),
    )
    METODO_PAGO_CHOICES = (
        ('transferencia', 'Transferencia Bancaria'),
        ('tarjeta', 'Tarjeta de Crédito/Débito'),
        ('efectivo', 'Efectivo'),
    )
    apoderado = models.ForeignKey(Apoderado, on_delete=models.CASCADE, related_name='mensualidades')
    numero = models.PositiveIntegerField()
    monto_inicial = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Monto Inicial")
    monto = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name="Monto Final")
    descuentos_aplicados = models.CharField(max_length=500, default="Ninguno", verbose_name="Descuentos Aplicados")
    fecha_vencimiento = models.DateField()
    fecha_pago = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, null=True, blank=True)
    comprobante = models.FileField(upload_to='comprobantes/', null=True, blank=True)
    anio_escolar = models.ForeignKey(AnioEscolar, on_delete=models.CASCADE, related_name='mensualidades', null=True, blank=True)

    def __str__(self):
        return f"Mensualidad {self.numero} - {self.apoderado} ({self.estado})"
    
class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"OTP {self.code} for {self.user.username}"