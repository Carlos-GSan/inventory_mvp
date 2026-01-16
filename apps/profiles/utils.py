from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.urls import reverse
from email.mime.image import MIMEImage
import os

def send_activation_email(employee):
    """Envía email con link de activación"""
    token = employee.generate_activation_token()
    activation_link = f"{settings.SITE_URL}{reverse('activate_account', kwargs={'token': token})}"
    
    # Verificar si existe el logo
    logo_path = os.path.join(settings.MEDIA_ROOT, 'logo.png')
    has_logo = os.path.exists(logo_path)
    
    subject = 'Activa tu cuenta - DisiTech'
    
    # Mensaje de texto plano (fallback)
    text_message = f"""
Hola {employee.first_name},

Tu cuenta de empleado ha sido creada en DisiTech.

Para activar tu acceso a la plataforma, haz clic en el siguiente enlace:
{activation_link}

Deberás crear tu nombre de usuario y contraseña.

Este enlace expira en 48 horas.

Saludos,
Equipo DisiTech
    """
    
    # Mensaje HTML con estilos
    html_message = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #2d2d2d 100%); min-height: 100vh; padding: 40px 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: linear-gradient(145deg, #ffffff 0%, #f5f5f5 100%); border-radius: 8px; overflow: hidden; box-shadow: 0 25px 50px rgba(0,0,0,0.5);">
            <!-- Header con línea de color -->
            <div style="height: 4px; background: linear-gradient(90deg, #b91c1c 0%, #cd7f32 50%, #b91c1c 100%);"></div>
            
            <!-- Logo -->
            <div style="text-align: center; padding: 40px 40px 20px 40px;">
                {f'<img src="cid:logo" alt="DisiTech Logo" style="max-width: 180px; height: auto; display: block; margin: 0 auto;">' if has_logo else '<div style="width: 120px; height: 120px; margin: 0 auto; background: linear-gradient(135deg, #1a1a1a 0%, #0a0a0a 100%); border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; font-size: 2.5rem; color: #cd7f32; font-weight: 700; border: 3px solid #b91c1c; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">DT</div>'}
            </div>
            
            <!-- Acentos industriales -->
            <div style="display: flex; justify-content: center; gap: 8px; margin-bottom: 24px;">
                <span style="width: 40px; height: 3px; background: #cd7f32; border-radius: 2px; display: inline-block;"></span>
                <span style="width: 40px; height: 3px; background: #cd7f32; border-radius: 2px; display: inline-block;"></span>
                <span style="width: 40px; height: 3px; background: #cd7f32; border-radius: 2px; display: inline-block;"></span>
            </div>
            
            <!-- Contenido -->
            <div style="padding: 0 40px 40px 40px;">
                <h1 style="text-align: center; font-size: 1.75rem; font-weight: 700; color: #0a0a0a; margin-bottom: 8px; letter-spacing: -0.5px;">
                    ¡Bienvenido, {employee.first_name}!
                </h1>
                
                <p style="text-align: center; color: #666; margin-bottom: 32px; font-size: 0.95rem;">
                    Tu cuenta de empleado ha sido creada en DisiTech
                </p>
                
                <p style="color: #333; margin-bottom: 24px; line-height: 1.6;">
                    Para activar tu acceso a la plataforma, haz clic en el siguiente botón:
                </p>
                
                <!-- Botón CTA -->
                <div style="text-align: center; margin: 32px 0;">
                    <a href="{activation_link}" style="display: inline-block; padding: 16px 40px; background: linear-gradient(135deg, #b91c1c 0%, #991b1b 100%); color: white; text-decoration: none; border-radius: 6px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; box-shadow: 0 10px 25px rgba(185, 28, 28, 0.3);">
                        Activar Mi Cuenta
                    </a>
                </div>
                
                <p style="color: #666; font-size: 0.9rem; margin-top: 24px; line-height: 1.6;">
                    Deberás crear tu nombre de usuario y contraseña.
                </p>
                
                <p style="color: #666; font-size: 0.9rem; margin-top: 16px; line-height: 1.6;">
                    <strong>Nota:</strong> Este enlace expira en 48 horas.
                </p>
                
                <p style="color: #666; font-size: 0.85rem; margin-top: 32px; padding-top: 24px; border-top: 1px solid #e0e0e0; line-height: 1.6;">
                    Si no puedes hacer clic en el botón, copia y pega el siguiente enlace en tu navegador:<br>
                    <a href="{activation_link}" style="color: #b91c1c; word-break: break-all;">{activation_link}</a>
                </p>
            </div>
            
            <!-- Footer -->
            <div style="text-align: center; padding: 24px; background: #f8f9fa; border-top: 1px solid #e0e0e0; color: #666; font-size: 0.85rem;">
                © 2025 DisiTech - Servicios Industriales de Ingeniería
            </div>
        </div>
    </body>
    </html>
    """
    
    # Crear email con versión HTML y texto plano
    email = EmailMultiAlternatives(
        subject,
        text_message,
        settings.DEFAULT_FROM_EMAIL,
        [employee.email]
    )
    email.attach_alternative(html_message, "text/html")
    
    # Adjuntar logo como imagen embebida si existe
    if has_logo:
        with open(logo_path, 'rb') as f:
            logo_data = f.read()
            logo_image = MIMEImage(logo_data)
            logo_image.add_header('Content-ID', '<logo>')
            logo_image.add_header('Content-Disposition', 'inline', filename='logo.png')
            email.attach(logo_image)
    
    email.send(fail_silently=False)