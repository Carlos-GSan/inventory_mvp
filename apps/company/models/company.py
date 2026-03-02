from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from apps.common.utils import generate_unique_filename


class Company(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    email = models.EmailField(unique=True, verbose_name="Correo electrónico")
    website = models.URLField(blank=True, verbose_name="Sitio web")
    logo = models.ImageField(upload_to="company_logo/", blank=True, null=True, verbose_name="Logo")

    def __str__(self):
        return self.name

    def clean(self):
        if not self.pk and Company.objects.exists():
            raise ValidationError("Solo puede existir una empresa registrada.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        
