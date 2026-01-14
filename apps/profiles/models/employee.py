"""
Modelos de la aplicación de usuario.
"""
from phonenumber_field.modelfields import PhoneNumberField
from django.db import models
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta

class Employee(models.Model):
    """Empleado - puede o no tener acceso a plataforma"""
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        null=True, 
        blank=True,
        related_name='employee_profile',
        help_text='Usuario creado cuando el empleado completa su registro'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = PhoneNumberField(unique=True, blank=True, null=True, region="MX")
    position = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    hire_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    # Token de activación
    activation_token = models.CharField(max_length=100, blank=True, null=True)
    activation_token_created = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'employees'
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def has_platform_access(self):
        """Verifica si tiene acceso activo a la plataforma"""
        return self.user is not None and self.is_active and self.user.is_active
    
    def generate_activation_token(self):
        """Genera token único para activación"""
        self.activation_token = get_random_string(64)
        self.activation_token_created = timezone.now()
        self.save()
        return self.activation_token
    
    def is_token_valid(self, token):
        """Verifica si el token es válido (48 horas)"""
        if not self.activation_token or self.activation_token != token:
            return False
        
        if not self.activation_token_created:
            return False
        
        expiration = self.activation_token_created + timedelta(hours=48)
        return timezone.now() < expiration
    
    def activate_account(self, username, password):
        """Crea el usuario cuando el empleado completa el registro"""
        if not self.user:
            self.user = User.objects.create_user(
                username=username,
                email=self.email,
                first_name=self.first_name,
                last_name=self.last_name,
                password=password,
                is_active=True
            )
            self.activation_token = None  # Invalidar token
            self.activation_token_created = None
            self.save()
            return True
        return False
    
    def save(self, *args, **kwargs):
        # Si empleado se desactiva, desactivar su usuario
        if not self.is_active and self.user:
            self.user.is_active = False
            self.user.save()
        super().save(*args, **kwargs)