from django.core.mail import send_mail
from django.conf import settings

def send_activation_email(employee):
    """Envía email con link de activación"""
    token = employee.generate_activation_token()
    activation_link = f"{settings.SITE_URL}/activate/{token}/"
    
    subject = 'Activa tu cuenta - DisiTech'
    message = f"""
Hola {employee.first_name},

Tu cuenta de empleado ha sido creada en DisiTech.

Para activar tu acceso a la plataforma, haz clic en el siguiente enlace:
{activation_link}

Deberás crear tu nombre de usuario y contraseña.

Este enlace expira en 48 horas.

Saludos,
Equipo DisiTech
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [employee.email],
        fail_silently=False,
    )