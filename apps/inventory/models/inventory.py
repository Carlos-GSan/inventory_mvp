from django.db import models
from django.core.exceptions import ValidationError

from apps.common.utils import normalize_name, generate_unique_filename


def item_photo_path(instance, filename):
    return generate_unique_filename(instance, filename, "item_photos")


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.name
    
    def clean(self):
        super().clean()
        if self.name:
            normalized = normalize_name(self.name)
            qs = Category.objects.all()
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            for cat in qs:
                if normalize_name(cat.name) == normalized:
                    raise ValidationError(
                        {"name": f'Ya existe una categoría similar: "{cat.name}".'}
                    )
    
    def save(self, *args, **kwargs):
        self.name = " ".join(self.name.split())  # limpiar espacios extra
        self.full_clean()
        super().save(*args, **kwargs)
    
    
class InventoryItem(models.Model):
    sku = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="items")
    
    description = models.CharField(max_length=250, unique=True)
    
    stock = models.PositiveIntegerField()
    min_stock = models.PositiveIntegerField()
    max_stock = models.PositiveIntegerField()
    
    active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["category", "active"]),
            models.Index(fields=["slug"]),
        ]
        
    def __str__(self):
        return f"{self.sku} - {self.description}"


class ItemPhoto(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField("imagen", upload_to=item_photo_path)
    caption = models.CharField("descripción", max_length=100, blank=True, default="")
    order = models.PositiveSmallIntegerField("orden", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Foto de producto"
        verbose_name_plural = "Fotos de producto"
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"Foto de {self.item.sku} - {self.caption or self.pk}"