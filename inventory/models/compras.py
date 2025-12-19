from django.db import models
from django.core.validators import MinValueValidator
from .inventory import InventoryItem

class Supplier(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name


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