"""Supplier views — thin controllers delegating to supplier service."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import JsonResponse

from ..models.purchases import Supplier
from ..services import suppliers as supplier_svc


@login_required
@permission_required("inventory.view_supplier", raise_exception=True)
def supplier_list(request):
    """Lista de proveedores con filtros y paginación."""
    search = request.GET.get("search", "")
    status = request.GET.get("status", "")
    suppliers = supplier_svc.get_supplier_list(search=search, status=status)

    per_page = request.GET.get("per_page", "10")
    try:
        per_page = int(per_page)
        if per_page not in [10, 20, 45]:
            per_page = 10
    except ValueError:
        per_page = 10

    paginator = Paginator(suppliers, per_page)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    context = {
        "page_obj": page_obj,
        "per_page": per_page,
        "search": search,
        "status": status,
    }

    if request.headers.get("HX-Request"):
        return render(request, "suppliers/partials/suppliers_table.html", context)
    return render(request, "suppliers/list.html", context)


@login_required
@permission_required("inventory.add_supplier", raise_exception=True)
def supplier_create(request):
    """Crear nuevo proveedor."""
    if request.method == "POST":
        try:
            supplier = supplier_svc.create_supplier(
                name=request.POST["name"],
                contact_name=request.POST.get("contact_name", ""),
                phone=request.POST.get("phone", "") or None,
                email=request.POST.get("email", ""),
                rfc=request.POST.get("rfc", "").upper(),
                address=request.POST.get("address", ""),
                active="active" in request.POST,
            )
            if request.headers.get("HX-Request"):
                return JsonResponse({"id": supplier.id, "name": supplier.name})
            messages.success(request, f'Proveedor "{supplier.name}" creado exitosamente')
            return redirect("supplier_list")
        except ValidationError as e:
            error_msg = (
                "; ".join(msg for msgs in e.message_dict.values() for msg in msgs)
                if hasattr(e, "message_dict")
                else str(e)
            )
            if request.headers.get("HX-Request"):
                return JsonResponse({"error": error_msg}, status=400)
            messages.error(request, error_msg)
        except Exception as e:
            if request.headers.get("HX-Request"):
                return JsonResponse({"error": str(e)}, status=400)
            messages.error(request, f"Error al crear proveedor: {e}")

    context = {"title": "Nuevo Proveedor", "form": {}}
    return render(request, "suppliers/form.html", context)


@login_required
@permission_required("inventory.change_supplier", raise_exception=True)
def supplier_update(request, pk):
    """Actualizar proveedor existente."""
    supplier = get_object_or_404(Supplier, pk=pk)

    if request.method == "POST":
        try:
            supplier_svc.update_supplier(
                supplier,
                name=request.POST["name"],
                contact_name=request.POST.get("contact_name", ""),
                phone=request.POST.get("phone", "") or None,
                email=request.POST.get("email", ""),
                rfc=request.POST.get("rfc", "").upper(),
                address=request.POST.get("address", ""),
                active="active" in request.POST,
            )
            messages.success(request, f'Proveedor "{supplier.name}" actualizado exitosamente')
            return redirect("supplier_list")
        except ValidationError as e:
            error_msg = (
                "; ".join(msg for msgs in e.message_dict.values() for msg in msgs)
                if hasattr(e, "message_dict")
                else str(e)
            )
            messages.error(request, error_msg)
        except Exception as e:
            messages.error(request, f"Error al actualizar proveedor: {e}")

    context = {
        "title": "Editar Proveedor",
        "supplier": supplier,
        "form": {
            "name": {"value": supplier.name},
            "contact_name": {"value": supplier.contact_name},
            "phone": {"value": str(supplier.phone) if supplier.phone else ""},
            "email": {"value": supplier.email},
            "rfc": {"value": supplier.rfc},
            "address": {"value": supplier.address},
            "active": {"value": supplier.active},
        },
    }
    return render(request, "suppliers/form.html", context)
