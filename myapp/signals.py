from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Apoderado, Descuento

@receiver(post_save, sender=Apoderado)
def actualizar_mensualidades(sender, instance, created, **kwargs):
    if instance.fecha_inicio:  # Solo si fecha_inicio está definida
        instance.calcular_mensualidades()

@receiver(post_save, sender=Descuento)
def actualizar_mensualidades_descuento(sender, instance, **kwargs):
    instance.apoderado.calcular_mensualidades()