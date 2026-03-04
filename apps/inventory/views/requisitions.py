"""Requisition views — thin controllers delegating to requisition service."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator

from ..models.inventory import InventoryItem
from ..models.transactions import Requisition
from ..services.purchases import parse_form_lines
from ..services import requisitions as requisition_svc


@login_required
@permission_required("inventory.view_requisition", raise_exception=True)
def requisition_list(request):
    """Lista de requisiciones con filtros y paginación."""
    if request.user.is_staff:
        requisitions = Requisition.objects.select_related("requested_by").order_by("-requested_at")
    else:
        requisitions = (
            Requisition.objects.filter(requested_by=request.user)
            .select_related("requested_by")
            .order_by("-requested_at")
        )

    solicitante_id = request.GET.get("solicitante", "")
    if request.user.is_staff and solicitante_id:
        requisitions = requisitions.filter(requested_by_id=solicitante_id)

    per_page = request.GET.get("per_page", "10")
    try:
        per_page = int(per_page)
        if per_page not in [10, 20, 45]:
            per_page = 10
    except ValueError:
        per_page = 10

    paginator = Paginator(requisitions, per_page)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    solicitantes = None
    if request.user.is_staff:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        solicitantes = (
            User.objects.filter(requisitions__isnull=False)
            .distinct()
            .order_by("first_name", "last_name", "username")
        )

    context = {
        "page_obj": page_obj,
        "per_page": per_page,
        "solicitantes": solicitantes,
        "solicitante_id": solicitante_id,
    }

    if request.headers.get("HX-Request"):
        return render(request, "requisitions/partials/requisitions_table.html", context)
    return render(request, "requisitions/list.html", context)


@login_required
@permission_required("inventory.add_requisition", raise_exception=True)
def requisition_create(request):
    """Crear nueva requisición."""
    if request.method == "POST":
        try:
            lines_data = parse_form_lines(request.POST)
            requisition = requisition_svc.create_requisition(
                user=request.user,
                requested_at=request.POST["requested_at"],
                note=request.POST.get("note", ""),
                lines_data=lines_data,
            )
            messages.success(request, f"Requisición #{requisition.id} creada exitosamente")
            return redirect("requisition_detail", pk=requisition.pk)
        except Exception as e:
            messages.error(request, f"Error al crear requisición: {e}")

    context = {"items": InventoryItem.objects.filter(active=True).order_by("sku")}
    return render(request, "requisitions/create.html", context)


@login_required
@permission_required("inventory.view_requisition", raise_exception=True)
def requisition_detail(request, pk):
    """Detalle de una requisición."""
    requisition = get_object_or_404(Requisition, pk=pk)
    if not request.user.is_staff and requisition.requested_by != request.user:
        raise PermissionDenied("No tienes permiso para ver esta requisición.")
    return render(request, "requisitions/detail.html", {"requisition": requisition})
