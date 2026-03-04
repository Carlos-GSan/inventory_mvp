"""Inventory item views — thin controllers delegating to inventory service."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator

from ..models.inventory import Category, InventoryItem
from ..services import inventory as inventory_svc


@login_required
@permission_required("inventory.view_inventoryitem", raise_exception=True)
def inventory_list(request):
    """Lista de inventario con filtros y paginación."""
    search = request.GET.get("search", "")
    category_id = request.GET.get("category", "")

    items = inventory_svc.get_inventory_list(search=search, category_id=category_id)

    per_page = request.GET.get("per_page", "10")
    try:
        per_page_int = int(per_page)
        if per_page_int not in [10, 20, 45]:
            per_page_int = 10
    except (ValueError, TypeError):
        per_page_int = 10

    paginator = Paginator(items, per_page_int)
    items_page = paginator.get_page(request.GET.get("page", 1))

    context = {
        "items": items_page,
        "categories": Category.objects.all(),
        "search": search,
        "category_id": category_id,
        "per_page": per_page,
    }

    if request.headers.get("HX-Request"):
        return render(request, "inventory/partials/inventory_table.html", context)
    return render(request, "inventory/list.html", context)


@login_required
@permission_required("inventory.add_inventoryitem", raise_exception=True)
def inventory_create(request):
    """Crear nuevo producto."""
    if request.method == "POST":
        try:
            item = inventory_svc.create_item(
                sku=request.POST["sku"],
                slug=request.POST["slug"],
                category_id=request.POST["category"],
                description=request.POST["description"],
                stock=int(request.POST["stock"]),
                min_stock=int(request.POST["min_stock"]),
                max_stock=int(request.POST["max_stock"]),
                active="active" in request.POST,
                photos=request.FILES.getlist("photos"),
            )
            messages.success(request, f"Producto {item.sku} creado exitosamente")
            return redirect("inventory_list")
        except Exception as e:
            messages.error(request, f"Error al crear producto: {e}")

    context = {
        "title": "Nuevo Producto",
        "categories": Category.objects.all(),
        "form": {},
    }
    return render(request, "inventory/form.html", context)


@login_required
@permission_required("inventory.change_inventoryitem", raise_exception=True)
def inventory_update(request, pk):
    """Actualizar producto existente."""
    item = get_object_or_404(InventoryItem, pk=pk)

    if request.method == "POST":
        try:
            inventory_svc.update_item(
                item,
                sku=request.POST["sku"],
                slug=request.POST["slug"],
                category_id=request.POST["category"],
                description=request.POST["description"],
                stock=int(request.POST["stock"]),
                min_stock=int(request.POST["min_stock"]),
                max_stock=int(request.POST["max_stock"]),
                active="active" in request.POST,
                photos=request.FILES.getlist("photos"),
            )
            messages.success(request, f"Producto {item.sku} actualizado exitosamente")
            return redirect("inventory_list")
        except Exception as e:
            messages.error(request, f"Error al actualizar producto: {e}")

    context = {
        "title": "Editar Producto",
        "categories": Category.objects.all(),
        "photos": item.photos.all(),
        "item": item,
        "form": {
            "sku": {"value": item.sku},
            "slug": {"value": item.slug},
            "description": {"value": item.description},
            "category": {"value": item.category_id},
            "stock": {"value": item.stock},
            "min_stock": {"value": item.min_stock},
            "max_stock": {"value": item.max_stock},
            "active": {"value": item.active},
        },
    }
    return render(request, "inventory/form.html", context)


@login_required
@permission_required("inventory.view_inventoryitem", raise_exception=True)
def inventory_print_label(request, pk):
    """Imprimir etiqueta con código de barras del producto."""
    item = get_object_or_404(InventoryItem, pk=pk, active=True)
    return render(request, "inventory/print_label.html", {"item": item})


@login_required
@permission_required("inventory.view_inventoryitem", raise_exception=True)
def inventory_print_labels(request):
    """Imprimir múltiples etiquetas con códigos de barras."""
    ids_str = request.GET.get("ids", "")

    if not ids_str:
        messages.error(request, "No se seleccionaron productos")
        return redirect("inventory_list")

    try:
        ids = [int(s.strip()) for s in ids_str.split(",") if s.strip()]
        items = InventoryItem.objects.filter(pk__in=ids, active=True).select_related("category")
        if not items.exists():
            messages.error(request, "No se encontraron productos válidos")
            return redirect("inventory_list")
        return render(request, "inventory/print_labels.html", {"items": items})
    except ValueError:
        messages.error(request, "IDs de productos inválidos")
        return redirect("inventory_list")


@login_required
@permission_required("inventory.change_inventoryitem", raise_exception=True)
def inventory_adjust(request, pk):
    """Ajustar stock de un producto."""
    item = get_object_or_404(InventoryItem, pk=pk)

    if request.method == "POST":
        try:
            qty = int(request.POST["qty"])
            note = request.POST.get("note", "")
            inventory_svc.adjust_stock(item, qty=qty, note=note)
            messages.success(
                request,
                f"Stock de {item.sku} ajustado exitosamente. Nuevo stock: {item.stock}",
            )
            return redirect("inventory_list")
        except Exception as e:
            messages.error(request, f"Error al ajustar stock: {e}")

    return render(request, "inventory/adjust.html", {"item": item})
