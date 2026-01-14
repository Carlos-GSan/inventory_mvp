from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from .inventory import InventoryItem
from .purchases import Supplier, Purchase

from django.conf import settings

class Requisition(models.Model):
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="requisitions")
    requested_at = models.DateField()
    note = models.CharField(max_length=300, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Req #{self.id} - {self.requested_by} - {self.requested_at}"


class RequisitionLine(models.Model):
    requisition = models.ForeignKey(Requisition, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name="requisition_lines")

    qty = models.IntegerField()

    def __str__(self):
        return f"{self.item.sku} x {self.qty}"
    

class InventoryTxn(models.Model):
    TXN_PURCHASE = "PURCHASE"
    TXN_ISSUE = "ISSUE"
    TXN_ADJUST = "ADJUST"

    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT, related_name="txns")
    txn_type = models.CharField(max_length=20, choices=[
        (TXN_PURCHASE, "Purchase"),
        (TXN_ISSUE, "Issue"),
        (TXN_ADJUST, "Adjust"),
    ])

    qty = models.IntegerField()  # + entra, - sale
    unit_price = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)  # si aplica

    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.PROTECT)
    purchase = models.ForeignKey(Purchase, null=True, blank=True, on_delete=models.CASCADE)
    requisition = models.ForeignKey(Requisition, null=True, blank=True, on_delete=models.CASCADE)

    happened_at = models.DateTimeField()
    note = models.CharField(max_length=300, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["happened_at"]),
            models.Index(fields=["item", "happened_at"]),
        ]