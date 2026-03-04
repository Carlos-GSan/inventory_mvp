from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField

from apps.common.utils import normalize_name, generate_unique_filename
from .inventory import InventoryItem


def purchase_photo_path(instance, filename):
    return generate_unique_filename(instance, filename, "purchase_photos")


class Supplier(models.Model):
    name = models.CharField("nombre", max_length=120, unique=True)
    contact_name = models.CharField("contacto principal", max_length=150, blank=True, default="")
    phone = PhoneNumberField("teléfono", blank=True, null=True, region="MX")
    email = models.EmailField("correo electrónico", blank=True, default="")
    rfc = models.CharField("RFC", max_length=13, blank=True, default="", db_index=True)
    address = models.TextField("dirección", blank=True, default="")
    active = models.BooleanField("activo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.name:
            normalized = normalize_name(self.name)
            qs = Supplier.objects.all()
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            for s in qs:
                if normalize_name(s.name) == normalized:
                    raise ValidationError(
                        {"name": f'Ya existe un proveedor similar: "{s.name}".'}
                    )

    def save(self, *args, **kwargs):
        self.name = " ".join(self.name.split())
        self.full_clean()
        super().save(*args, **kwargs)


class Purchase(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchases")
    purchased_at = models.DateField()
    ref = models.CharField(max_length=80, null=True, blank=True)  # folio/factura/OC
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Purchase #{self.id} - {self.supplier} - {self.purchased_at}"


class PurchaseLine(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name="purchase_lines")
    qty = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=14, decimal_places=4, validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.item.sku} x {self.qty}"


class PurchasePhoto(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField("imagen", upload_to=purchase_photo_path)
    caption = models.CharField("descripción", max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Foto de compra"
        verbose_name_plural = "Fotos de compra"
        ordering = ["created_at"]

    def __str__(self):
        return f"Foto de Compra #{self.purchase_id} - {self.caption or self.pk}"