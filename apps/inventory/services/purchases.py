"""
Business logic for purchases with stock management.

Purchase creation / edition / deletion atomically maintains stock consistency
by pairing every stock change with an ``InventoryTxn`` record.
"""

import json
import re

from django.db import transaction
from django.utils import timezone

from ..models.inventory import InventoryItem
from ..models.purchases import Purchase, PurchaseLine, PurchasePhoto
from ..models.transactions import InventoryTxn


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_form_lines(post_data):
    """Parse purchase/requisition form lines with format ``lines[0][field]``."""
    lines_data = {}
    pattern = re.compile(r"lines\[(\d+)\]\[(\w+)\]")
    for key, value in post_data.items():
        match = pattern.match(key)
        if match:
            idx, field = match.group(1), match.group(2)
            lines_data.setdefault(idx, {})[field] = value
    return lines_data


def _validate_lines(lines_data, *, require_price=True):
    """Return list of valid line dicts; raise if none are valid."""
    valid = []
    for ld in lines_data.values():
        has_basics = ld.get("item") and ld.get("qty")
        if require_price:
            has_basics = has_basics and ld.get("unit_price")
        if has_basics:
            valid.append(ld)
    if not valid:
        raise ValueError("Debe agregar al menos un producto")
    return valid


# ---------------------------------------------------------------------------
# Commands (write)
# ---------------------------------------------------------------------------

def create_purchase(*, supplier_id, purchased_at, ref="", lines_data, photos=None):
    """Create a purchase, update stock, record transactions, attach photos."""
    valid_lines = _validate_lines(lines_data)

    with transaction.atomic():
        purchase = Purchase.objects.create(
            supplier_id=supplier_id,
            purchased_at=purchased_at,
            ref=ref,
        )

        for ld in valid_lines:
            item = InventoryItem.objects.select_for_update().get(pk=ld["item"])
            qty = int(ld["qty"])
            unit_price = float(ld["unit_price"])

            PurchaseLine.objects.create(
                purchase=purchase, item=item, qty=qty, unit_price=unit_price,
            )
            item.stock += qty
            item.save()

            InventoryTxn.objects.create(
                item=item,
                txn_type=InventoryTxn.TXN_PURCHASE,
                qty=qty,
                unit_price=unit_price,
                supplier=purchase.supplier,
                purchase=purchase,
                happened_at=timezone.now(),
                note=f"Compra #{purchase.id}",
            )

        for photo in photos or []:
            PurchasePhoto.objects.create(purchase=purchase, image=photo)

    return purchase


def update_purchase(purchase, *, supplier_id, purchased_at, ref="", lines_data, photos=None):
    """Revert original stock, delete old lines/txns, apply new ones, attach photos."""
    valid_lines = _validate_lines(lines_data)

    with transaction.atomic():
        # 1) Revert stock from original lines
        for line in purchase.lines.select_related("item"):
            item = InventoryItem.objects.select_for_update().get(pk=line.item_id)
            item.stock -= line.qty
            item.save()

        # 2) Delete old transactions and lines
        InventoryTxn.objects.filter(purchase=purchase).delete()
        purchase.lines.all().delete()

        # 3) Update header
        purchase.supplier_id = supplier_id
        purchase.purchased_at = purchased_at
        purchase.ref = ref
        purchase.save()

        # 4) Create new lines
        for ld in valid_lines:
            item = InventoryItem.objects.select_for_update().get(pk=ld["item"])
            qty = int(ld["qty"])
            unit_price = float(ld["unit_price"])

            PurchaseLine.objects.create(
                purchase=purchase, item=item, qty=qty, unit_price=unit_price,
            )
            item.stock += qty
            item.save()

            InventoryTxn.objects.create(
                item=item,
                txn_type=InventoryTxn.TXN_PURCHASE,
                qty=qty,
                unit_price=unit_price,
                supplier=purchase.supplier,
                purchase=purchase,
                happened_at=timezone.now(),
                note=f"Compra #{purchase.id} (editada)",
            )

        # 5) Attach new photos
        for photo in photos or []:
            PurchasePhoto.objects.create(purchase=purchase, image=photo)

    return purchase


def delete_purchase(purchase):
    """Revert stock and delete purchase (CASCADE removes lines, photos, txns)."""
    with transaction.atomic():
        for line in purchase.lines.select_related("item"):
            item = InventoryItem.objects.select_for_update().get(pk=line.item_id)
            item.stock -= line.qty
            item.save()
        purchase.delete()


# ---------------------------------------------------------------------------
# Queries (read)
# ---------------------------------------------------------------------------

def get_purchase_detail(purchase):
    """Enrich purchase with lines subtotals and total; returns purchase."""
    lines = list(purchase.lines.select_related("item").all())
    total = 0
    for line in lines:
        line.subtotal = line.qty * line.unit_price
        total += line.subtotal
    purchase.total = total
    purchase.lines_with_subtotal = lines
    return purchase


def get_purchase_edit_context(purchase):
    """Return existing lines as a JSON string for the edit form JS."""
    existing_lines = []
    for line in purchase.lines.select_related("item"):
        existing_lines.append({
            "item_id": line.item_id,
            "item_text": f"{line.item.sku} - {line.item.description}",
            "qty": line.qty,
            "unit_price": str(line.unit_price),
        })
    return json.dumps(existing_lines)
