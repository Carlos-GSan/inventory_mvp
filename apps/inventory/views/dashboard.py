"""Dashboard view — thin controller delegating to dashboard service."""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from ..models.inventory import InventoryItem
from ..services import dashboard as dashboard_svc


@login_required
def dashboard(request):
    """Dashboard principal con estadísticas."""
    stats = dashboard_svc.get_stats(request.user)
    low_stock_items = dashboard_svc.get_low_stock_items(request.user)

    # Transactions with filters & pagination
    item_filter = request.GET.get("item", "")
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")

    txn_qs = dashboard_svc.get_transactions_qs(request.user)
    txn_qs = dashboard_svc.filter_transactions(
        txn_qs, item_filter=item_filter, date_from=date_from, date_to=date_to,
    )

    paginator = Paginator(txn_qs, 10)
    recent_transactions = paginator.get_page(request.GET.get("page", 1))

    all_items = (
        InventoryItem.objects.filter(active=True)
        .values("id", "sku", "description")
        .order_by("sku")
    )

    context = {
        "stats": stats,
        "low_stock_items": low_stock_items,
        "recent_transactions": recent_transactions,
        "all_items": all_items,
        "item_filter": item_filter,
        "date_from": date_from,
        "date_to": date_to,
    }

    if request.headers.get("HX-Request"):
        return render(request, "inventory/partials/transactions_table.html", context)
    return render(request, "dashboard.html", context)
