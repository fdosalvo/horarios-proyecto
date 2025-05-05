import os
import django
from django.core.mail import send_mail

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

# Enviar el correo de prueba
send_mail(
    'Prueba de Correo desde Django',
    'Este es un correo de prueba.',
    'no-reply@localhost',
    ['test@localhost'],  # Correo de destino (será capturado por MailHog)
    fail_silently=False,
)


