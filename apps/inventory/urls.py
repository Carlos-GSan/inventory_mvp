from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),
    
    # Inventario
    path("inventario/", views.inventory_list, name="inventory_list"),
    path("inventario/nuevo/", views.inventory_create, name="inventory_create"),
    path("inventario/<int:pk>/editar/", views.inventory_update, name="inventory_update"),
    path("inventario/<int:pk>/ajustar/", views.inventory_adjust, name="inventory_adjust"),
    path("inventario/<int:pk>/etiqueta/", views.inventory_print_label, name="inventory_print_label"),
    path("inventario/etiquetas/", views.inventory_print_labels, name="inventory_print_labels"),
    
    # Proveedores
    path("proveedores/", views.supplier_list, name="supplier_list"),
    path("proveedores/nuevo/", views.supplier_create, name="supplier_create"),
    path("proveedores/<int:pk>/editar/", views.supplier_update, name="supplier_update"),

    # Categorías
    path("categorias/", views.category_list, name="category_list"),
    path("categorias/nueva/", views.category_create, name="category_create"),
    path("categorias/<int:pk>/editar/", views.category_update, name="category_update"),

    # Compras
    path("compras/", views.purchase_list, name="purchase_list"),
    path("compras/nueva/", views.purchase_create, name="purchase_create"),
    path("compras/<int:pk>/", views.purchase_detail, name="purchase_detail"),
    path("compras/<int:pk>/editar/", views.purchase_update, name="purchase_update"),
    path("compras/<int:pk>/eliminar/", views.purchase_delete, name="purchase_delete"),
    
    # Requisiciones
    path("requisiciones/", views.requisition_list, name="requisition_list"),
    path("requisiciones/nueva/", views.requisition_create, name="requisition_create"),
    path("requisiciones/<int:pk>/", views.requisition_detail, name="requisition_detail"),

    # Fotos (HTMX)
    path("fotos/producto/<int:pk>/eliminar/", views.item_photo_delete, name="item_photo_delete"),
    path("fotos/compra/<int:pk>/eliminar/", views.purchase_photo_delete, name="purchase_photo_delete"),
]
