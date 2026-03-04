"""
Business logic for inventory items.

All write operations are wrapped in ``transaction.atomic()`` and receive
keyword-only arguments so callers are explicit about every field.
"""

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from ..models.inventory import Category, InventoryItem, ItemPhoto
from ..models.transactions import InventoryTxn


# ---------------------------------------------------------------------------
# Commands (write)
# ---------------------------------------------------------------------------

def create_item(
    *,
    sku,
    slug,
    category_id,
    description,
    stock,
    min_stock,
    max_stock,
    active,
    photos=None,
):
    """Create a new inventory item with optional photos."""
    with transaction.atomic():
        item = InventoryItem.objects.create(
            sku=sku,
            slug=slug,
            category_id=category_id,
            description=description,
            stock=stock,
            min_stock=min_stock,
            max_stock=max_stock,
            active=active,
        )
        for photo in photos or []:
            ItemPhoto.objects.create(item=item, image=photo)
    return item


def update_item(
    item,
    *,
    sku,
    slug,
    category_id,
    description,
    stock,
    min_stock,
    max_stock,
    active,
    photos=None,
):
    """Update an existing inventory item and optionally add new photos."""
    with transaction.atomic():
        item.sku = sku
        item.slug = slug
        item.category_id = category_id
        item.description = description
        item.stock = stock
        item.min_stock = min_stock
        item.max_stock = max_stock
        item.active = active
        item.save()
        for photo in photos or []:
            ItemPhoto.objects.create(item=item, image=photo)
    return item


def adjust_stock(item, *, qty, note=""):
    """Adjust stock level and record an ADJUST transaction."""
    with transaction.atomic():
        item.stock += qty
        item.save()
        InventoryTxn.objects.create(
            item=item,
            txn_type=InventoryTxn.TXN_ADJUST,
            qty=qty,
            happened_at=timezone.now(),
            note=note,
        )
    return item


# ---------------------------------------------------------------------------
# Queries (read)
# ---------------------------------------------------------------------------

def get_inventory_list(*, search="", category_id=""):
    """Return filtered queryset of active inventory items."""
    qs = (
        InventoryItem.objects
        .filter(active=True)
        .select_related("category")
        .prefetch_related("photos")
    )
    if search:
        qs = qs.filter(
            Q(sku__icontains=search) | Q(description__icontains=search)
        )
    if category_id:
        qs = qs.filter(category_id=category_id)
    return qs.order_by("sku")
