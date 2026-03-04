"""
Business logic for requisitions with stock validation.

Each requisition line reduces stock and records an ISSUE transaction.
"""

from django.db import transaction
from django.utils import timezone

from ..models.inventory import InventoryItem
from ..models.transactions import Requisition, RequisitionLine, InventoryTxn
from .purchases import _validate_lines


# ---------------------------------------------------------------------------
# Commands (write)
# ---------------------------------------------------------------------------

def create_requisition(*, user, requested_at, note="", lines_data):
    """Create a requisition, validate & reduce stock, record transactions."""
    valid_lines = _validate_lines(lines_data, require_price=False)

    with transaction.atomic():
        requisition = Requisition.objects.create(
            requested_by=user,
            requested_at=requested_at,
            note=note,
        )

        for ld in valid_lines:
            item = InventoryItem.objects.select_for_update().get(pk=ld["item"])
            qty = int(ld["qty"])

            if item.stock < qty:
                raise ValueError(
                    f"Stock insuficiente para {item.sku}. "
                    f"Disponible: {item.stock}, Solicitado: {qty}"
                )

            RequisitionLine.objects.create(
                requisition=requisition, item=item, qty=qty,
            )
            item.stock -= qty
            item.save()

            InventoryTxn.objects.create(
                item=item,
                txn_type=InventoryTxn.TXN_ISSUE,
                qty=-qty,
                requisition=requisition,
                happened_at=timezone.now(),
                note=f"Requisición #{requisition.id}",
            )

    return requisition
