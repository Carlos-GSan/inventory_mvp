"""Photo deletion views (HTMX endpoints)."""

from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse

from ..services import photos as photo_svc


@login_required
@permission_required("inventory.change_inventoryitem", raise_exception=True)
def item_photo_delete(request, pk):
    """Eliminar foto de producto (HTMX)."""
    if request.method == "POST":
        photo_svc.delete_item_photo(pk)
        return JsonResponse({"ok": True})
    return JsonResponse({"error": "Método no permitido"}, status=405)


@login_required
@permission_required("inventory.change_purchase", raise_exception=True)
def purchase_photo_delete(request, pk):
    """Eliminar foto de compra (HTMX)."""
    if request.method == "POST":
        photo_svc.delete_purchase_photo(pk)
        return JsonResponse({"ok": True})
    return JsonResponse({"error": "Método no permitido"}, status=405)
