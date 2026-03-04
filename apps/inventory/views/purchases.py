"""Purchase views — thin controllers delegating to purchase service."""

import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from ..models.inventory import InventoryItem
from ..models.purchases import Supplier, Purchase
from ..services import purchases as purchase_svc


@login_required
@permission_required("inventory.view_purchase", raise_exception=True)
def purchase_list(request):
    """Lista de compras con filtros y paginación."""
    purchases = (
        Purchase.objects.select_related("supplier")
        .prefetch_related("lines")
        .order_by("-purchased_at")
    )

    supplier_id = request.GET.get("supplier", "")
    if supplier_id:
        purchases = purchases.filter(supplier_id=supplier_id)

    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    if date_from:
        purchases = purchases.filter(purchased_at__gte=date_from)
    if date_to:
        purchases = purchases.filter(purchased_at__lte=date_to)

    ref = request.GET.get("ref", "")
    if ref:
        purchases = purchases.filter(ref__icontains=ref)

    q = request.GET.get("q", "")
    if q:
        purchases = purchases.filter(
            Q(ref__icontains=q)
            | Q(supplier__name__icontains=q)
            | Q(lines__item__description__icontains=q)
            | Q(lines__item__sku__icontains=q)
        ).distinct()

    for p in purchases:
        p.total = sum(line.qty * line.unit_price for line in p.lines.all())

    per_page = request.GET.get("per_page", "10")
    try:
        per_page = int(per_page)
        if per_page not in [10, 20, 45]:
            per_page = 10
    except ValueError:
        per_page = 10

    paginator = Paginator(purchases, per_page)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    context = {
        "page_obj": page_obj,
        "per_page": per_page,
        "suppliers": Supplier.objects.order_by("name"),
        "supplier_id": supplier_id,
        "date_from": date_from,
        "date_to": date_to,
        "ref": ref,
        "q": q,
    }

    if request.headers.get("HX-Request"):
        return render(request, "purchases/partials/purchases_table.html", context)
    return render(request, "purchases/list.html", context)


@login_required
@permission_required("inventory.add_purchase", raise_exception=True)
def purchase_create(request):
    """Crear nueva compra."""
    if request.method == "POST":
        try:
            lines_data = purchase_svc.parse_form_lines(request.POST)
            purchase = purchase_svc.create_purchase(
                supplier_id=request.POST["supplier"],
                purchased_at=request.POST["purchased_at"],
                ref=request.POST.get("ref", ""),
                lines_data=lines_data,
                photos=request.FILES.getlist("photos"),
            )
            messages.success(request, f"Compra #{purchase.id} creada exitosamente")
            return redirect("purchase_detail", pk=purchase.pk)
        except Exception as e:
            messages.error(request, f"Error al crear compra: {e}")

    context = {
        "suppliers": Supplier.objects.all(),
        "items": InventoryItem.objects.filter(active=True).order_by("sku"),
    }
    return render(request, "purchases/create.html", context)


@login_required
@permission_required("inventory.view_purchase", raise_exception=True)
def purchase_detail(request, pk):
    """Detalle de una compra."""
    purchase = get_object_or_404(Purchase, pk=pk)
    purchase_svc.get_purchase_detail(purchase)
    return render(request, "purchases/detail.html", {"purchase": purchase})


@login_required
@permission_required("inventory.change_purchase", raise_exception=True)
def purchase_update(request, pk):
    """Editar compra existente — revierte transacciones originales y aplica las nuevas."""
    purchase = get_object_or_404(Purchase, pk=pk)

    if request.method == "POST":
        try:
            lines_data = purchase_svc.parse_form_lines(request.POST)
            purchase_svc.update_purchase(
                purchase,
                supplier_id=request.POST["supplier"],
                purchased_at=request.POST["purchased_at"],
                ref=request.POST.get("ref", ""),
                lines_data=lines_data,
                photos=request.FILES.getlist("photos"),
            )
            messages.success(request, f"Compra #{purchase.id} actualizada exitosamente")
            return redirect("purchase_detail", pk=purchase.pk)
        except Exception as e:
            messages.error(request, f"Error al actualizar compra: {e}")

    context = {
        "title": f"Editar Compra #{purchase.id}",
        "purchase": purchase,
        "suppliers": Supplier.objects.filter(active=True).order_by("name"),
        "items": InventoryItem.objects.filter(active=True).order_by("sku"),
        "existing_lines": purchase_svc.get_purchase_edit_context(purchase),
        "photos": purchase.photos.all(),
        "is_edit": True,
    }
    return render(request, "purchases/edit.html", context)


@login_required
@permission_required("inventory.delete_purchase", raise_exception=True)
def purchase_delete(request, pk):
    """Eliminar compra — revierte stock y elimina todo."""
    purchase = get_object_or_404(Purchase, pk=pk)

    if request.method == "POST":
        try:
            purchase_id = purchase.id
            purchase_svc.delete_purchase(purchase)
            messages.success(request, f"Compra #{purchase_id} eliminada y stock revertido")
        except Exception as e:
            messages.error(request, f"Error al eliminar compra: {e}")
            return redirect("purchase_detail", pk=pk)

    return redirect("purchase_list")
