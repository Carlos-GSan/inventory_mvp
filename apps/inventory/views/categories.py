"""Category views — thin controllers delegating to category service."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator

from ..models.inventory import Category
from ..services import categories as category_svc


@login_required
@permission_required("inventory.view_category", raise_exception=True)
def category_list(request):
    """Lista de categorías con filtros y paginación."""
    search = request.GET.get("search", "")
    categories = category_svc.get_category_list(search=search)

    per_page = request.GET.get("per_page", "10")
    try:
        per_page = int(per_page)
        if per_page not in [10, 20, 45]:
            per_page = 10
    except ValueError:
        per_page = 10

    paginator = Paginator(categories, per_page)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    context = {"page_obj": page_obj, "per_page": per_page, "search": search}

    if request.headers.get("HX-Request"):
        return render(request, "categories/partials/categories_table.html", context)
    return render(request, "categories/list.html", context)


@login_required
@permission_required("inventory.add_category", raise_exception=True)
def category_create(request):
    """Crear nueva categoría."""
    if request.method == "POST":
        try:
            category = category_svc.create_category(name=request.POST["name"])
            messages.success(request, f'Categoría "{category.name}" creada exitosamente')
            return redirect("category_list")
        except ValidationError as e:
            error_msg = (
                "; ".join(msg for msgs in e.message_dict.values() for msg in msgs)
                if hasattr(e, "message_dict")
                else str(e)
            )
            messages.error(request, error_msg)
        except Exception as e:
            messages.error(request, f"Error al crear categoría: {e}")

    context = {"title": "Nueva Categoría", "form": {}}
    return render(request, "categories/form.html", context)


@login_required
@permission_required("inventory.change_category", raise_exception=True)
def category_update(request, pk):
    """Actualizar categoría existente."""
    category = get_object_or_404(Category, pk=pk)

    if request.method == "POST":
        try:
            category_svc.update_category(category, name=request.POST["name"])
            messages.success(request, f'Categoría "{category.name}" actualizada exitosamente')
            return redirect("category_list")
        except ValidationError as e:
            error_msg = (
                "; ".join(msg for msgs in e.message_dict.values() for msg in msgs)
                if hasattr(e, "message_dict")
                else str(e)
            )
            messages.error(request, error_msg)
        except Exception as e:
            messages.error(request, f"Error al actualizar categoría: {e}")

    context = {
        "title": "Editar Categoría",
        "category": category,
        "form": {"name": {"value": category.name}},
    }
    return render(request, "categories/form.html", context)
