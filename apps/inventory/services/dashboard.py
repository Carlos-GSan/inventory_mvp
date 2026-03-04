"""
Dashboard statistics and transaction queries.
"""

from datetime import datetime

from django.db.models import Q, F
from django.utils import timezone

from ..models.inventory import InventoryItem
from ..models.purchases import Purchase
from ..models.transactions import Requisition, InventoryTxn


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

def get_stats(user):
    """Return dashboard statistics dict based on user role."""
    now = timezone.now()
    first_day = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if user.is_staff:
        return {
            "total_items": InventoryItem.objects.filter(active=True).count(),
            "low_stock_items": InventoryItem.objects.filter(
                active=True, stock__lte=F("min_stock")
            ).count(),
            "total_purchases": Purchase.objects.filter(created_at__gte=first_day).count(),
            "total_requisitions": Requisition.objects.filter(created_at__gte=first_day).count(),
        }

    return {
        "total_items": 0,
        "low_stock_items": 0,
        "total_purchases": 0,
        "total_requisitions": Requisition.objects.filter(
            requested_by=user, created_at__gte=first_day
        ).count(),
    }


def get_low_stock_items(user):
    """Return low-stock items (admin only)."""
    if not user.is_staff:
        return InventoryItem.objects.none()
    return (
        InventoryItem.objects
        .filter(active=True, stock__lte=F("min_stock"))
        .select_related("category")
        .order_by("stock")[:10]
    )


def get_transactions_qs(user):
    """Return base transactions queryset scoped to user role."""
    qs = InventoryTxn.objects.select_related(
        "item", "supplier", "purchase", "requisition"
    )
    if not user.is_staff:
        qs = qs.filter(requisition__requested_by=user)
    return qs


def filter_transactions(qs, *, item_filter="", date_from="", date_to=""):
    """Apply optional filters to a transactions queryset."""
    if item_filter:
        qs = qs.filter(
            Q(item__sku__icontains=item_filter)
            | Q(item__description__icontains=item_filter)
        )
    if date_from:
        try:
            qs = qs.filter(
                happened_at__gte=datetime.strptime(date_from, "%Y-%m-%d")
            )
        except ValueError:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59
            )
            qs = qs.filter(happened_at__lte=dt)
        except ValueError:
            pass
    return qs.order_by("-happened_at")
